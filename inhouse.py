import trueskill
import cassiopeia as cass
import pandas as pd
import json
import glob
from match_processing import output_ratings, compute_ratings, parser
from matchmaking import do_matchmaking
from match_stats import output_plots, show_player_wr_by_champ, plot_elo_history
from match_pull import pull_latest_match
from pathlib import Path
import settings

#trueskill
trueskill.setup(backend="scipy", draw_probability=0)
cass.set_riot_api_key(settings.api_key)

def parse_match_database(inhouse_data_path):
    game_files = sorted(glob.glob(str(Path(inhouse_data_path) / '*.json')))
    matches = pd.DataFrame.from_records([parser(json.dumps(json.load(open(x)))) for x in game_files])
    return matches

def generate_matchups(ratings, participants):
    #input is like
    #participants= ['Ai Lan Ball', 'ANiceSunset', 'BathSalt', 'bobzillas', 'Bradnon', 'ClappityBunny', 'FatYthaar', 'Namikami', 'TensorFlow', ('newplayer1', '20, 32064')]
    matchups, messages = do_matchmaking(ratings, participants, PLAYER_ROLE_PREF)
    return matchups, messages

def get_player_stats(ign, out_dir, fn=None):
    matches = parse_match_database(settings.json_dir)
    messages = show_player_wr_by_champ(matches, ign)
    ratings, *_ = compute_ratings(matches, settings.filter, settings.sort_metric)
    plot_elo_history(ratings, ign, out_dir, fn)
    return messages

def update_results(tournament_code, known_ign, out_dir):
    if tournament_code is not None:
        pull_messages = pull_latest_match(known_ign, tournament_code, api_key, json_dir)
    else:
        pull_messages = None
    matches = parse_match_database(json_dir)
    ratings, wins, losses, totals_with, totals_against = compute_ratings(matches,filter,sort_metric)
    output_ratings(ratings,False,out_dir)
    draft_messages = output_plots(matches, ratings, wins, losses, totals_with, totals_against, out_dir)
    return pull_messages, draft_messages

def inhouse_function(participants):
    matches = parse_match_database(settings.json_dir)
    ratings, *_ = compute_ratings(matches, False, settings.sort_metric)
    matchups, messages = generate_matchups(ratings, participants)
    return matchups, messages

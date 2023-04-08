
import trueskill
from cassiopeia import Summoner
import cassiopeia as cass
import numpy as np
import pandas as pd
import random
import itertools
import bisect
import os
import json
import ipywidgets as widgets
import IPython
import requests
import collections
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import time
import configparser
from match_processing import output_ratings, compute_ratings, parser
from matchmaking import do_matchmaking
from match_stats import output_plots, show_player_wr_by_champ, plot_elo_history
from match_pull import pull_latest_match
import argparse
from pathlib import Path
    
config = configparser.ConfigParser()
config.read("config/inhouse.cfg")

#secret key
api_key = config['API']['api_key']

#trueskill
trueskill.setup(backend="scipy", draw_probability=0)
filter=bool(config['RATINGS']['filter'])
sort_metric = config['RATINGS']['sort_metric']

cass.set_riot_api_key(api_key)

json_dir = config['DATA']['json_dir']

smurf_filename = config['USERDATA']['smurfs']
with open(smurf_filename,'r') as f:
    SMURFS = json.load(f)

rolepref_filename = config['USERDATA']['rolepref']
with open(rolepref_filename,'r') as f:
    PLAYER_ROLE_PREF = json.load(f)

version = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
champs = requests.get('https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json'.format(version)).json()
CHAMP_ICON_URL = 'https://ddragon.leagueoflegends.com/cdn/{}/img/champion/{{}}.png'.format(version)
champs_by_key = {int(champ['key']): champ for champ in champs['data'].values()}

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
    matches = parse_match_database(json_dir)
    messages = show_player_wr_by_champ(matches, ign)
    ratings, wins, losses, totals_with, totals_against = compute_ratings(matches,filter,sort_metric)
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
    matches = parse_match_database(json_dir)
    ratings, wins, losses, totals_with, totals_against = compute_ratings(matches,False,sort_metric)
    matchups, messages = generate_matchups(ratings, participants)
    return matchups, messages
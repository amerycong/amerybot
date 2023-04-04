import trueskill
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

smurf_filename = 'smurfs.json'
with open(smurf_filename,'r') as f:
    SMURFS = json.load(f)

rolepref_filename = 'rolepref.json'
with open(rolepref_filename,'r') as f:
    PLAYER_ROLE_PREF = json.load(f)

version = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
champs = requests.get('https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json'.format(version)).json()
CHAMP_ICON_URL = 'https://ddragon.leagueoflegends.com/cdn/{}/img/champion/{{}}.png'.format(version)
champs_by_key = {int(champ['key']): champ for champ in champs['data'].values()}


def get_canonical_name(name):
    return SMURFS[name] if name in SMURFS else name

def parser(raw):
  if 'metadata' in json.loads(raw).keys():
    return parse_match(raw)
  else:
    return parse_old_match(raw)

def parse_match(raw):
    match = json.loads(raw)
    
    match_id = match["info"]["gameId"]    
    match_duration = match["info"]["gameDuration"]
    identities = {
        pid["participantId"]: {"summonerName": pid["summonerName"]} for pid in match['info']['participants']
    }

    win_team, loss_team = (
        next(team["teamId"] for team in match["info"]["teams"] if team["win"] == result)
        for result in (True, False)
    )

    win, loss = (
        tuple(
            get_canonical_name(identities[p["participantId"]]["summonerName"])
            for p in match['info']['participants']
            if p["teamId"] == team
        )
        for team in (win_team, loss_team)
    )
    
    match_bans = [champs_by_key[x['championId']]['id'] for x in match["info"]["teams"][0]["bans"]+match["info"]["teams"][1]["bans"]]
    player_stats = {
        get_canonical_name(identities[p["participantId"]]["summonerName"]): {
              'win': p["win"],
              'kills': p["kills"],
              'deaths': p["deaths"],
              'assists': p["assists"],
              'role': p['role'],
              'lane': p['lane'],
              'cs_minion': p["totalMinionsKilled"],
              'cs_neutral': p["neutralMinionsKilled"],
              'vision': p["visionScore"],
              'gold': p["goldEarned"],
              'total_dmg_champs': p['totalDamageDealtToChampions'],
              #'cs_diff_10': p["timeline"]['csDiffPerMinDeltas']['0-10']*10 if 'csDiffPerMinDeltas' in p["timeline"].keys() and '0-10' in p["timeline"]['csDiffPerMinDeltas'].keys() else 0, #this shit bugged, not in all games
              #'cs_diff_20': p["timeline"]['csDiffPerMinDeltas']['0-10']*10+p["timeline"]['csDiffPerMinDeltas']['10-20']*10 if 'csDiffPerMinDeltas' in p["timeline"].keys() and '10-20' in p["timeline"]['csDiffPerMinDeltas'].keys() else 0, #cs diff unreliable for 20+30, ignores monsters
              #'cs_diff_30': p["timeline"]['csDiffPerMinDeltas']['0-10']*10+p["timeline"]['csDiffPerMinDeltas']['10-20']*10+p["timeline"]['csDiffPerMinDeltas']['20-30']*10 if 'csDiffPerMinDeltas' in p["timeline"].keys() and '20-30' in p["timeline"]['csDiffPerMinDeltas'].keys() else 0, #cs diff unreliable for 20+30, ignores monsters
              'champ': champs_by_key[p['championId']]['id'],
              'match_duration': match_duration
        }
        for p in match['info']['participants']
    }

    return pd.Series({
        'match_id': match_id,
        'win': win,
        'loss': loss,
        'bans': match_bans,
        'player_stats': player_stats,
    })

def parse_old_match(raw):
    match = json.loads(raw)
    
    match_id = match["gameId"]    
    match_duration = match["gameDuration"]
    identities = {
        pid["participantId"]: pid["player"] for pid in match["participantIdentities"]
    }

    win_team, loss_team = (
        next(team["teamId"] for team in match["teams"] if team["win"] == result)
        for result in ("Win", "Fail")
    )

    win, loss = (
        tuple(
            get_canonical_name(identities[p["participantId"]]["summonerName"])
            for p in match["participants"]
            if p["teamId"] == team
        )
        for team in (win_team, loss_team)
    )
    
    match_bans = [champs_by_key[x['championId']]['id'] for x in match["teams"][0]["bans"]+match["teams"][1]["bans"]]
    player_stats = {
        get_canonical_name(identities[p["participantId"]]["summonerName"]): {
              'win': p["stats"]["win"],
              'kills': p["stats"]["kills"],
              'deaths': p["stats"]["deaths"],
              'assists': p["stats"]["assists"],
              'role': p['timeline']['role'],
              'lane': p['timeline']['lane'],
              'cs_minion': p["stats"]["totalMinionsKilled"],
              'cs_neutral': p["stats"]["neutralMinionsKilled"],
              'vision': p["stats"]["visionScore"],
              'gold': p["stats"]["goldEarned"],
              'total_dmg_champs': p["stats"]['totalDamageDealtToChampions'],
              'cs_diff_10': p["timeline"]['csDiffPerMinDeltas']['0-10']*10 if 'csDiffPerMinDeltas' in p["timeline"].keys() and '0-10' in p["timeline"]['csDiffPerMinDeltas'].keys() else 0, #this shit bugged, not in all games
              'cs_diff_20': p["timeline"]['csDiffPerMinDeltas']['0-10']*10+p["timeline"]['csDiffPerMinDeltas']['10-20']*10 if 'csDiffPerMinDeltas' in p["timeline"].keys() and '10-20' in p["timeline"]['csDiffPerMinDeltas'].keys() else 0, #cs diff unreliable for 20+30, ignores monsters
              'cs_diff_30': p["timeline"]['csDiffPerMinDeltas']['0-10']*10+p["timeline"]['csDiffPerMinDeltas']['10-20']*10+p["timeline"]['csDiffPerMinDeltas']['20-30']*10 if 'csDiffPerMinDeltas' in p["timeline"].keys() and '20-30' in p["timeline"]['csDiffPerMinDeltas'].keys() else 0, #cs diff unreliable for 20+30, ignores monsters
              'champ': champs_by_key[p['championId']]['id'],
              'match_duration': match_duration
        }
        for p in match["participants"]
    }
    if False:
      #stats with shitters
      b= 'ANiceSunset'
      a= 'Ahrizona'
      if a in player_stats.keys() and b in player_stats.keys():
        if (a in win and b in win) or (a in loss and b in loss):
          player_stats[a+' ('+b+')']=player_stats.pop(a)
          win = tuple([x.replace(a,a+' ('+b+')') for x in list(win)])
          loss = tuple([x.replace(a,a+' ('+b+')') for x in list(loss)])

    if False:
      #jg only stats (shit junglers)
      for n in ['TensorFlow']:
        if n in player_stats.keys():
          if player_stats[n]['lane']=='JUNGLE':
            player_stats[n+' (jungle)']=player_stats.pop(n)
            win = tuple([x.replace(n,n+' (jungle)') for x in list(win)])
            loss = tuple([x.replace(n,n+' (jungle)') for x in list(loss)])
    if False:
      #lane only stats (jg in lane lul)
      for n in ['MrRgrs', 'ZoSo']:       
        if n in player_stats.keys():
          if player_stats[n]['lane']!='JUNGLE':
            player_stats[n+' (lane)']=player_stats.pop(n)
            win = tuple([x.replace(n,n+' (lane)') for x in list(win)])
            loss = tuple([x.replace(n,n+' (lane)') for x in list(loss)])
    if False:
      #adc only stats 
      for n in ['ANiceSunset','Ahrizona','Kurtzorz']:       
        if n in player_stats.keys():
          if (player_stats[n]['role']!='DUO_SUPPORT') and (player_stats[n]['lane']=='BOTTOM'):
            player_stats[n+' (adc)']=player_stats.pop(n)
            win = tuple([x.replace(n,n+' (adc)') for x in list(win)])
            loss = tuple([x.replace(n,n+' (adc)') for x in list(loss)])

    return pd.Series({
        'match_id': match_id,
        'win': win,
        'loss': loss,
        'bans': match_bans,
        'player_stats': player_stats,
    })


def compute_division_boundaries():
    divisions = [
        "{} {}".format(tier, division)
        for tier in [
            "8086",
            "Celeron",
            "Pentium",
            "Core i3",
            "Core i5",
            "Core i7",
            "Core i9",
            "Xeon",
        ]
        for division in ["IV", "III", "II", "I"]
    ]
    division_boundaries = [(float("-inf"), divisions[0])]
    min_rating = trueskill.global_env().mu - 3 * trueskill.global_env().sigma
    max_rating = trueskill.global_env().mu + 3 * trueskill.global_env().sigma
    division_boundaries.extend(
        (
            min_rating + i * (max_rating - min_rating) / (len(divisions) - 1),
            divisions[i + 1],
        )
        for i in range(len(divisions) - 1)
    )
    return division_boundaries


def find_division(boundaries, rating):
    chally = False
    prev_cutoff = boundaries[bisect.bisect(boundaries, (rating, "")) - 1][0]
    try:
      next_cutoff = boundaries[bisect.bisect(boundaries, (rating, ""))][0]
    except:
      chally = True
    if prev_cutoff == -np.inf:
      lp_diff = boundaries[2][0]-boundaries[1][0]
      lp = int(round(100-(next_cutoff-rating)/lp_diff*100))
    elif chally:
      lp_diff = boundaries[-1][0]-boundaries[-2][0]
      lp = int(round((rating-prev_cutoff)/lp_diff*100))
    else:
      lp = int(round((rating-prev_cutoff)/(next_cutoff-prev_cutoff)*100))
    return boundaries[bisect.bisect(boundaries, (rating, "")) - 1][1]+' '+str(lp)+' LP'

def compute_record(stats):
    win = sum(1 for game in stats if game and game["win"])
    loss = sum(1 for game in stats if game and not game["win"])
    return "{:.0%} ({}W {}L)".format(win / (win + loss), win, loss)


def compute_streak(stats):
    last_result = None
    count = 0
    for game in stats[::-1]:
        if game != None:
            if last_result == None:
                last_result = game["win"]
            if game["win"] == last_result:
                count += 1
            else:
                break
    return "{}{}".format(count, "W" if last_result else "L")

def compute_kda(stats,string=True):
    num_games = sum(1 for game in stats if game)
    kills = sum(game['kills'] for game in stats if game) / num_games
    deaths = sum(game['deaths'] for game in stats if game) / num_games
    assists = sum(game['assists'] for game in stats if game) / num_games
    kda =  (kills + assists) / max(1,deaths)
    if string:
      return "{:.1f} / {:.1f} / {:.1f} ({:.1f})".format(kills, deaths, assists, kda)
    else:
      return kda
  
def compute_gametime(stats):
    total_game_duration = sum(game['match_duration']/60.0 for game in stats if game)
    num_games = sum(1 for game in stats if game)
    gametime = total_game_duration / num_games
    return "{:.2f}".format(gametime)

def compute_cspm(stats):
    total_game_duration = sum(game['match_duration']/60.0 for game in stats if game if game['role'] not in ['DUO_SUPPORT'])#not (game['role'] in ['DUO_SUPPORT'] and game['lane'] in ['BOTTOM']))
    if total_game_duration == 0:
      return "-1"
    cspm = sum(game['cs_minion']+game['cs_neutral'] for game in stats if game if game['role'] not in ['DUO_SUPPORT']) / total_game_duration#not (game['role'] in ['DUO_SUPPORT'] and game['lane'] in ['BOTTOM'])) / total_game_duration
    return "{:.1f}".format(cspm)

def compute_visionpm(stats):
    total_game_duration = sum(game['match_duration']/60.0 for game in stats if game)# if game['role'] not in ['DUO_SUPPORT'])
    #num_games = sum(1 for game in stats if game)
    if total_game_duration == 0:
      return "-1"
    #vision_score = sum(game['vision'] for game in stats if game) / num_games
    visionpm = sum(game['vision'] for game in stats if game) / total_game_duration
    return "{:.2f}".format(visionpm)

def compute_dmgpm(stats):
    total_game_duration = sum(game['match_duration']/60.0 for game in stats if game if game['role'] not in ['DUO_SUPPORT'])
    if total_game_duration == 0:
      return "-1"
    dmg = sum(game['total_dmg_champs'] for game in stats if game if game['role'] not in ['DUO_SUPPORT']) / total_game_duration
    return "{:.0f}".format(dmg)

def compute_dmgpg(stats):
    total_gold = sum(game['gold'] for game in stats if game if game['role'] not in ['DUO_SUPPORT'])
    if total_gold == 0:
      return "-1"
    dmg = sum(game['total_dmg_champs'] for game in stats if game if game['role'] not in ['DUO_SUPPORT']) / total_gold
    return "{:.2f}".format(dmg)

def compute_gpm(stats):
    total_game_duration = sum(game['match_duration']/60.0 for game in stats if game if game['role'] not in ['DUO_SUPPORT'])
    if total_game_duration == 0:
      return "-1"
    gpm = sum(game['gold'] for game in stats if game if game['role'] not in ['DUO_SUPPORT']) / total_game_duration
    return "{:.0f}".format(gpm)

def compute_csdiff(stats,time=10):
    #time = 10,20,30
    num_games = sum(1 for game in stats if game if 'cs_diff_'+str(time) in game.keys() if game['role'] not in ['DUO_SUPPORT'] if game['lane'] not in ['JUNGLE'])
    if num_games == 0:
      return "-1"
    csdiff = sum(game['cs_diff_'+str(time)] for game in stats if game if 'cs_diff_'+str(time) in game.keys() if game['role'] not in ['DUO_SUPPORT'] if game['lane'] not in ['JUNGLE']) / num_games
    return "{:.1f}".format(csdiff)

def compute_dick_length(stats):
    total_num_champs = len(champs['data'])
    num_games = sum(1 for game in stats if game)
    num_unique_champs = len(set([game["champ"] for game in stats if game]))
    if num_unique_champs == total_num_champs:
      dick_length = 12
    else:
      bde = num_unique_champs / num_games
      avg_pp_size = 3.61
      min_games = 30 #negative activeness if under this amount of games played
      avg_champ_pool = 15 #benchmark for pos/neg pool size influence
      avg_bde = 0.5 #benchmark for champ variety (0.5 = 1 new champ every 2 games)
      gamma = 0.3 #scaling for pool multiplier
      champ_pool_multiplier = (num_unique_champs/avg_champ_pool)**gamma
      champ_playrate_std = np.std(list(collections.Counter([x['champ'] for x in stats if x != None]).values()))
      variance_influence = 0.01 #amount of influence variance can have
      variance_multiplier = 1-variance_influence*champ_playrate_std
      bde_multiplier = bde/avg_bde
      base_activeness = 0.25
      activeness_multiplier = ((1-base_activeness)/min_games)*num_games+base_activeness if num_games < min_games else 1
      dick_length = avg_pp_size*champ_pool_multiplier*variance_multiplier*bde_multiplier*activeness_multiplier

    return "{:.2f}".format(dick_length)


def compute_ratings(matches,filter=False,sort_metric='Rating'):

    intel_list = ['TensorFlow', 'TensorFlow (jungle)', 'TensorFlow (bobz)',
        'MrRgrs', 'MrRgrs (lane)','TheGatorMan', 'Omarlitle', 
        'Miss Viper', 'Miss Viper (jungle)','Dokgaebi', 'RageMuffinz', 
        'ClappityBunny', 'bobzillas',
        'Orcamaster','Demacian Smite ',
        'ANiceSunset', 'ANiceSunset (adc)', 'ANiceSunset (Ahrizona)',
        'icaneataberger', 'Namikami','Namikami (lane)', 
        'Bradnon', 'Mindpalace', 'ZoSo',
        'Shragon','CantonNeko','BathSalt', 'Snekky', 'IIIDemigodIII', 
        'Time Engineer', 'Im Tushikatotem', 'FatYthaar', 'Jacmert', 'Speedy Boykins',
        'Projective Cat', 'RectumHoward', 'Ai Lan Ball']
    inactive_intel_list = []
    guest_list = ['Hokari','Skullchaos','Agani']

    filter_list = intel_list + guest_list

    ratings = {}
    histories = {}
    new_player_history = []
    stats = {}
    new_player_stats = []
    wins = collections.defaultdict(dict)
    losses = collections.defaultdict(dict)
    totals_with = collections.defaultdict(dict)
    totals_against  = collections.defaultdict(dict)
    for _, match in matches.iterrows():
        for name in set(itertools.chain(stats.keys(), match['player_stats'])):
            stats.setdefault(name, new_player_stats[:])
            if name in match['player_stats']:
                stats[name].append(match['player_stats'][name])
            else:
                stats[name].append(None)
        new_player_stats.append(None)
        new_ratings = trueskill.rate(
            (
                {name: ratings.get(name, trueskill.Rating()) for name in match["win"]},
                {name: ratings.get(name, trueskill.Rating()) for name in match["loss"]},
            )
        )
        for new_rating in new_ratings:
            ratings.update(new_rating)

        new_player_history.append(trueskill.Rating())
        for name in ratings:
            histories.setdefault(name, new_player_history[:])
            histories[name].append(ratings[name])

        all_ppl = match['win']+match['loss']
        for i in all_ppl:
          for j in all_ppl:
            if filter:
              if i not in filter_list or j not in filter_list:
                continue
            if (i in match['win']) == (j in match['win']):
              if i in totals_with.keys() and j in totals_with[i].keys():
                wins[i][j] += 1 if (i in match['win'] and j in match['win']) else 0
                totals_with[i][j] += 1
              else:
                wins[i][j] = 1 if (i in match['win'] and j in match['win']) else 0 
                totals_with[i][j] = 1 
            else:
              if i in totals_against.keys() and j in totals_against[i].keys():
                losses[i][j] += 1 if (i in match['loss'] and j in match['win']) else 0 
                totals_against[i][j] += 1
              else:
                losses[i][j] = 1 if (i in match['loss'] and j in match['win']) else 0 
                totals_against[i][j] = 1

    rows = [(name, rating, stats[name], histories[name]) for name, rating in ratings.items()]
    ratings = pd.DataFrame.from_records(
        rows, columns=["Name", "trueskill.Rating", "stats", "history"], index="Name"
    )
    ratings.index.name = None

    boundaries = compute_division_boundaries()
    ratings["μ"] = ratings["trueskill.Rating"].apply(lambda rating: rating.mu)
    ratings["σ"] = ratings["trueskill.Rating"].apply(lambda rating: rating.sigma)
    ratings["Rating"] = ratings["trueskill.Rating"].apply(
        lambda rating: trueskill.expose(rating)
    )
    ratings["Rank"] = ratings["Rating"].apply(
        lambda rating: find_division(boundaries, rating)
    )
    ratings["Record"] = ratings["stats"].apply(lambda stats: compute_record(stats))
    ratings["Streak"] = ratings["stats"].apply(lambda stats: compute_streak(stats))
    ratings["Champs"] = ratings["stats"].apply(lambda stats:
      tuple(game["champ"] for game in stats if game)
    )
    ratings["num_champs"] = ratings["stats"].apply(lambda stats:
      len(set(tuple(game["champ"] for game in stats if game)))
    )
    ratings["PP SIZE"] = ratings["stats"].apply(lambda stats: compute_dick_length(stats))
    ratings["KDA"] = ratings["stats"].apply(lambda stats: compute_kda(stats))
    ratings["kda_val"] = ratings["stats"].apply(lambda stats: compute_kda(stats,False))
    ratings["avg time"] = ratings["stats"].apply(lambda stats: compute_gametime(stats))
    ratings["CSpM"] = ratings["stats"].apply(lambda stats: compute_cspm(stats))
    ratings["GpM"] = ratings["stats"].apply(lambda stats: compute_gpm(stats))
    ratings["DMGpM"] = ratings["stats"].apply(lambda stats: compute_dmgpm(stats))
    ratings["DMGpG"] = ratings["stats"].apply(lambda stats: compute_dmgpg(stats))
    ratings["VisionpM"] = ratings["stats"].apply(lambda stats: compute_visionpm(stats))
    #ratings["CSdiff10"] = ratings["stats"].apply(lambda stats: compute_csdiff(stats,10))
    #ratings["CSdiff20"] = ratings["stats"].apply(lambda stats: compute_csdiff(stats,20))
    #ratings["CSdiff30"] = ratings["stats"].apply(lambda stats: compute_csdiff(stats,30))
    ratings.sort_values(sort_metric, ascending=False, inplace=True)

    if filter:
      ratings = ratings[ratings.index.isin(filter_list)]
    
    wins = pd.DataFrame(wins)
    wins = wins.reindex(sorted(wins.columns), axis=1)
    wins = wins.sort_index()
    losses = pd.DataFrame(losses)
    losses = losses.reindex(sorted(losses.columns), axis=1)
    losses = losses.sort_index()
    totals_with = pd.DataFrame(totals_with)
    totals_with = totals_with.reindex(sorted(totals_with.columns), axis=1)
    totals_with = totals_with.sort_index()
    totals_against = pd.DataFrame(totals_against)
    totals_against = totals_against.reindex(sorted(totals_against.columns), axis=1)
    totals_against = totals_against.sort_index()
    return ratings, wins, losses, totals_with, totals_against
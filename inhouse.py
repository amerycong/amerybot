
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
from match_processing import *
from matchmaking import *
from match_stats import *
from synergy import *
from match_pull import *
    
config = configparser.ConfigParser()
config.read("inhouse.cfg")

#code for last played match
tournament_code = config['MATCH']['tournament_code']
#ign of someone who played in that game
ign = config['MATCH']['ign']
pull_last_match = config['MATCH'].getboolean('pull_last_match')
#secret key
api_key = config['API']['api_key']

#trueskill
trueskill.setup(backend="scipy", draw_probability=0)
filter=bool(config['RATINGS']['filter'])
sort_metric = config['RATINGS']['sort_metric']

cass.set_riot_api_key(api_key)

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

def parse_match_database(inhouse_data_path = 'inhouse_game_data/'):
    game_files = sorted(glob.glob(inhouse_data_path+'*.json'))
    matches = pd.DataFrame.from_records([parser(json.dumps(json.load(open(x)))) for x in game_files])
    return matches

def generate_matchups(ratings, participants):
    #input is like
    #participants= ['Ai Lan Ball', 'ANiceSunset', 'BathSalt', 'bobzillas', 'Bradnon', 'ClappityBunny', 'FatYthaar', 'Namikami', 'TensorFlow', ('newplayer1', '20, 32064')]
    matchups = do_matchmaking(ratings, participants, PLAYER_ROLE_PREF)
    return matchups

def inhouse_function2(participants, STORED_CHANNEL):
    matchups = [['TheShy','Bengi','Faker','DoubleLift','TensorFlow'],['Junecake','Miss Viper','FillyBs','bobzillas','Yuumi Bot']]
    time.sleep(10)
    return matchups

def inhouse_function(participants, STORED_CHANNEL):
    if pull_last_match:
        messages = pull_latest_match(ign, tournament_code, api_key=api_key)
    matches = parse_match_database()
    ratings, wins, losses, totals_with, totals_against = compute_ratings(matches,filter,sort_metric)
    matchups = generate_matchups(ratings, participants)
    return matchups
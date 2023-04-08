import requests
import configparser
from dotenv import load_dotenv
import os
import json
load_dotenv()


TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

config = configparser.ConfigParser()
config.read("config/bot.cfg")
inhouse_config = configparser.ConfigParser()
inhouse_config.read("config/inhouse.cfg")


ENABLE_GDRIVE = config['GDRIVE'].getboolean('enable')
OUTPUT_CHANNEL_ID = int(config['OUTPUTS']['output_channel_id'])
OUT_DIR =  config['OUTPUTS']['output_dir']
DISCORD_IDS = config['DISCORD_IDS']
rolepref_fn = inhouse_config['USERDATA']['rolepref']
idmapping_fn = inhouse_config['USERDATA']['idmapping']
fileID = config['GDRIVE']['file_id']

last_tournament_code = inhouse_config['MATCH']['tournament_code']
default_ign = inhouse_config['MATCH']['ign']

api_key = inhouse_config['API']['api_key']
filter=bool(inhouse_config['RATINGS']['filter'])
sort_metric = inhouse_config['RATINGS']['sort_metric']

json_dir = inhouse_config['DATA']['json_dir']
smurf_filename = inhouse_config['USERDATA']['smurfs']
with open(smurf_filename,'r') as f:
    SMURFS = json.load(f)

rolepref_filename = config['USERDATA']['rolepref']
with open(rolepref_filename,'r') as f:
    PLAYER_ROLE_PREF = json.load(f)

intel_list_filename = config['USERDATA']['intel_list']
with open(intel_list_filename) as f:
    intel_list = [line.rstrip() for line in f]

guest_list_filename = config['USERDATA']['guest_list']
with open(guest_list_filename) as f:
    guest_list = [line.rstrip() for line in f]

version = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
champs = requests.get('https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json'.format(version)).json()
CHAMP_ICON_URL = 'https://ddragon.leagueoflegends.com/cdn/{}/img/champion/{{}}.png'.format(version)
champs_by_key = {int(champ['key']): champ for champ in champs['data'].values()}

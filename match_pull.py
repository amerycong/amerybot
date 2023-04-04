from cassiopeia import Summoner
import cassiopeia as cass
import requests
import json
import os
import numpy as np

def pull_latest_match(ign, tournament_code, api_key,json_dir='inhouse_game_data',notebook=False):
    cass.set_riot_api_key(api_key)

    messages = []
    
    tf = Summoner(name=ign,region="NA")
    match_ids = [x.id for x in tf.match_history]

    found_match = False
    for i,match_id in enumerate(match_ids):
        if str(match_id)[:3]!='NA1':
            old_match_id = match_id
            match_id = 'NA1_'+str(old_match_id)
            print('the fucking API sucks dick (inconsistent naming): '+str(old_match_id)+' -> '+match_id)
        match_history_call = "https://americas.api.riotgames.com/lol/match/v5/matches/"+match_id+"?api_key="+api_key

        x = requests.get(match_history_call)

        mh = json.loads(x.text)

        if mh['info']['tournamentCode']==tournament_code:
            found_match = True
            print('inhouse game found for '+ign+' '+str(i+1)+' game(s) ago! ('+match_id+')')
            #sanity check to make sure it's the right game
            print('=============================================')
            print('VERIFY TEAMS BELOW ARE ACCURATE FOR LAST GAME')
            print('=============================================')
            print('\n')
            team_ids = np.unique([mh['info']['participants'][i]['teamId'] for i in range(len(mh['info']['participants']))])
            match_participants = [print('team '+str(i+1)+': '+''.join(str([mh['info']['participants'][k]['summonerName']+' ('+mh['info']['participants'][k]['championName']+')' for k in range(len(mh['info']['participants'])) if mh['info']['participants'][k]['teamId']==j]))) for i,j in enumerate(team_ids)]
            print('\n')
            json_path = os.path.join(json_dir,match_id+'.json')
            #json_path = '/content/drive/MyDrive/inhouse_game_data/'+match_id+'.json'
            if os.path.isfile(json_path):
                game_exists_str = 'Game '+match_id+' already seems to be downloaded, double check?'
                messages.append(game_exists_str)
                print(game_exists_str)
            else:
                with open(json_path,'w') as f:
                    json.dump(mh,f,indent=4)
                game_added_str = 'Game '+match_id+' added to database!'
                messages.append(game_added_str)
                print(game_added_str)
            break
    if not found_match:
        no_found_match_str = "tournament code not found in match history"
        messages.append(no_found_match_str)
        print(no_found_match_str)
    return messages
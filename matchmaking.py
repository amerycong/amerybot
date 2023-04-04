import itertools
import random
import trueskill
import time
import numpy as np

PLAYERS_PER_SIDE = 5
PLAYERS_PER_GAME = PLAYERS_PER_SIDE * 2
ROLES = 'tjmas'
ROLE_PERMUTATIONS = [''.join(p) for p in itertools.permutations(ROLES)] 
random.shuffle(ROLE_PERMUTATIONS)

def get_role_pref(p,PLAYER_ROLE_PREF):
    pref = PLAYER_ROLE_PREF.get(p,ROLES)
    if len(pref)>5:
      pref = ROLES
    if pref.isnumeric():
      role_pref = ''.join([r for i,r in enumerate(ROLES) if pref[i] != '0'])
    else:
      role_pref = ROLES if pref=='f' else pref
    return role_pref

def do_matchmaking(ratings, current_players,PLAYER_ROLE_PREF,sortby='quality',notebook=False):
    messages = []
    # player_ratings = {
    #     player: ratings.loc[player, "trueskill.Rating"]
    #     for player in current_players
    # }
    player_ratings = {}
    for player in current_players:
        if type(player)==tuple:#',' in player:
            player_name = player[0]
            player_input = player[1]
            player_ratings[player_name] = trueskill.Rating(float(player_input.split(', ')[0]))
            PLAYER_ROLE_PREF[player_name] = player_input.split(', ')[1]
        else:
            player_ratings[player] = ratings.loc[player, "trueskill.Rating"]
    print(player_ratings)
    for i in range(PLAYERS_PER_GAME - len(current_players)):
        player_ratings["New player #{}".format(i + 1)] = trueskill.Rating()
    players = player_ratings.keys()

    def avg_mmr(team):
        return sum(player_ratings[player].mu for player in team) / PLAYERS_PER_SIDE

    def normalize_map(role_map):
        if not role_map.isnumeric():
            role_map = '11111' if role_map == 'f' else ''.join(['1' if r in role_map else '0' for r in ROLES])
        total = sum([float(j) for j in role_map])
        norm_map = [float(j)/total for j in role_map]
        return norm_map

    def happiness(team,team_roles):
        happiness = 0
        for i,player in enumerate(team):
            happiness_map = normalize_map(PLAYER_ROLE_PREF.get(player,ROLES))
            h = happiness_map[ROLES.index(team_roles[i])]
            if h == 0:
                return 0
            happiness+=h

        return happiness

    matchups = list()
    print('############################\nanalyzing role permutations...\n############################')
    start_anal = time.time()
    for team1 in itertools.combinations(players, PLAYERS_PER_SIDE):
        team2 = tuple(player for player in players if player not in team1)
        if avg_mmr(team1) > avg_mmr(team2):
            continue
        quality = trueskill.quality(
            (
                tuple(player_ratings[player] for player in team1),
                tuple(player_ratings[player] for player in team2),
            )
        )
        #find optimal role permutation if any
        max_happy = -1
        max_t1_h = -1
        max_t2_h = -1
        for t1_roles in ROLE_PERMUTATIONS:
            for t2_roles in ROLE_PERMUTATIONS:
                t1_happy = happiness(team1,t1_roles)
                t2_happy = happiness(team2,t2_roles)
                match_happiness = (t1_happy * t2_happy) / (1 + abs(t1_happy-t2_happy)) #maybe sqrt in denom for less harsh penalty
                if match_happiness>max_happy:
                    max_happy = match_happiness
                    max_t1_h = t1_happy
                    max_t2_h = t2_happy
                    team1_roles = [n+' ('+t1_roles[i]+')' for i,n in enumerate(team1)]
                    team2_roles = [n+' ('+t2_roles[i]+')' for i,n in enumerate(team2)]
        matchups.append((quality, max_t1_h, max_t2_h, max_happy, team1, team1_roles, team2, team2_roles))
    end_anal = time.time()-start_anal
    print('anal cumplete: '+str(end_anal)+'s')

    num_matchups_displayed = 10
    matchup_counter = 0
    quality_threshold = 0.5
    if sortby=='happiness':
        matchups.sort(key=lambda x: x[3], reverse=True)
    elif sortby=='quality':
        matchups.sort(reverse=True)
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$\nLISTING MATCHUPS BY '+sortby.upper()+'\n$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    for count, (quality, t1_happy, t2_happy, match_happiness, team1, team1_roles, team2, team2_roles) in enumerate(matchups):#[:12]:
        if matchup_counter==num_matchups_displayed or quality<quality_threshold:
            if quality<quality_threshold:
                continue#print('remaining matchup qualities are dogshit')
            break
        #check role satisfaction
        # t1_good = False
        # t1_roles= False
        # t2_roles= False
        # for rp in ROLE_PERMUTATIONS:
        #   if np.all([rp[i] in get_role_pref(p) for i,p in enumerate(team1)]):
        #     t1_roles = rp
        #     t1_good=True
        #     break  
        # if t1_good:
        #   for rp in ROLE_PERMUTATIONS:
        #     if np.all([rp[i] in get_role_pref(p) for i,p in enumerate(team2)]):
        #       t2_roles=rp
        #       break
        if match_happiness>0:#t1_roles and t2_roles:
            print("\n*********OPTION {}*********\nQuality {:.6f}\tHappiness Coefficient {:.3f}".format(matchup_counter+1,quality, match_happiness))
            team1_roles_pretty = ', '.join([team1_roles[z].ljust(20) for z in [np.where(['('+s+')' in t for t in team1_roles])[0][0] for s in ROLES]])
            team2_roles_pretty = ', '.join([team2_roles[z].ljust(20) for z in [np.where(['('+s+')' in t for t in team2_roles])[0][0] for s in ROLES]])
            team1_str = "Team 1 (avg MMR {:.3f}, happiness {:.3f}): {}".format(
                    avg_mmr(team1), t1_happy, team1_roles_pretty
                )
            team2_str = "Team 2 (avg MMR {:.3f}, happiness {:.3f}): {}".format(
                    avg_mmr(team2), t2_happy, team2_roles_pretty
                )
            if count==0: #maybe make more robust based on how many matchups, dont rely on counter
                messages.append(team1_str)
                messages.append(team2_str)
            print(team1_str)
            print(team2_str)
            matchup_counter+=1
        else:
            print('role assignment failed')
            # print("\nQuality {:.6f}".format(quality))
            # print(
            #     "Team 1 (average MMR {:.3f}): {}".format(
            #         avg_mmr(team1), ", ".join(team1)
            #     )
            # )
            # print(
            #     "Team 2 (average MMR {:.3f}): {}".format(
            #         avg_mmr(team2), ", ".join(team2)
            #     )
            # )
    if matchup_counter==0:
        no_valid_matchups_str = 'no valid matchups found'
        messages.append(no_valid_matchups_str)
        print(no_valid_matchups_str)
    
    return messages
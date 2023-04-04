def show_draft_stats(matches,num_shown=10,min_games=7):
  all_champs = [(x[y]['champ'],x[y]['win']) for x in matches['player_stats'] for y in list(x)]
  all_bans = [x for y in matches['bans'].tolist() for x in y]
  number_games_played = collections.Counter([x[0] for x in all_champs])
  most_played = number_games_played.most_common(num_shown)
  number_games_banned = collections.Counter(all_bans)
  most_banned = number_games_banned.most_common(num_shown)
  champ_wr = [(c,round(100*all_champs.count((c,True))/(all_champs.count((c,True))+all_champs.count((c,False))),2),number_games_played[c]) for c in np.unique([x[0] for x in all_champs]) if number_games_played[c]>=min_games]
  highest_wr = sorted(champ_wr, key= lambda x:x[1],reverse=True)[:num_shown]
  lowest_wr = sorted(champ_wr, key= lambda x:x[1])[:num_shown]
  fmt = '{:<20}{:<15}{:<20}{:<15}{:<20}{:<8}{:<15}{:<20}{:<8}{:<15}'
  print(fmt.format('most played champs','# games','most banned champs','# games','highest wr champs','% wr','# games','lowest wr champs','% wr','# games'))
  for i, (mp, mb, hw, lw) in enumerate(zip(most_played,most_banned,highest_wr,lowest_wr)):
    print(fmt.format(*mp,*mb,*hw,*lw))

def show_player_wr_by_champ(matches,name=''):
  if name != '':
    player = [(x[y]['champ'],x[y]['win']) for x in matches['player_stats'] for y in list(x) if y==name]
    champ_wr = [(c,player.count((c,True))/(player.count((c,True))+player.count((c,False))),collections.Counter([x[0] for x in player])[c]) for c in np.unique([x[0] for x in player])]
    champ_wr.sort(key=lambda x: x[-1], reverse=True)
    print('\n'+name)
    [print('{}: {:.2f}% {} games'.format(x,y*100,z)) for x,y,z in champ_wr]
    print('\n'+str(len(champ_wr))+' unique champs played')

def plot_elo_history(ratings,name_list):
  sns.set_theme(style="darkgrid")
  fig,ax = plt.subplots(figsize=(20,10))
  for n in name_list:
    sns.lineplot(data=[trueskill.expose(x) for x in ratings['history'][n]],ax=ax)
  plt.xlabel('Game #')
  plt.ylabel('Rating')
  plt.legend(name_list)

def plot_rank_dist(ratings,bw_method=None,type='rating'):
  fig,ax = plt.subplots(figsize=(20,10))
  ratings['Rating'].plot.kde(bw_method)
  plt.xlabel('Rating')
  plt.title(r'$\mu={:.2f}$ ({})'.format(ratings['Rating'].mean(),find_division(compute_division_boundaries(), ratings['Rating'].mean()).rsplit(' ',2)[0]))
  db = compute_division_boundaries()
  sb = [x for x in db if 'IV' in x[1]]+[(np.inf,'Peak IV')]
  rank_color = ['dimgray','peru','silver','gold','teal','royalblue','darkviolet','red']
  for i in range(len(sb)-1):
    start_idx = max(sb[i][0],plt.xlim()[0])
    end_idx = min(sb[i+1][0],plt.xlim()[1])
    plt.axvspan(start_idx,end_idx,alpha=0.5, color = rank_color[i])
import collections
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import trueskill
from match_processing import find_division, compute_division_boundaries
from pathlib import Path

def show_draft_stats(matches,num_shown=10,min_games=7):
  all_champs = [(x[y]['champ'],x[y]['win']) for x in matches['player_stats'] for y in list(x)]
  all_bans = [x for y in matches['bans'].tolist() for x in y]
  number_games_played = collections.Counter([x[0] for x in all_champs])
  most_played = number_games_played.most_common(num_shown)
  number_games_banned = collections.Counter(all_bans)
  most_banned = number_games_banned.most_common(num_shown)
  champ_wr = [
    (
      c,
      round(100*all_champs.count((c,True))/(all_champs.count((c,True))+all_champs.count((c,False))),2),
      number_games_played[c],
    )
    for c in np.unique([x[0] for x in all_champs])
    if number_games_played[c]>=min_games
  ]
  highest_wr = sorted(champ_wr, key= lambda x:x[1],reverse=True)[:num_shown]
  lowest_wr = sorted(champ_wr, key= lambda x:x[1])[:num_shown]
  fmt = '{:<20}{:<15}{:<20}{:<15}{:<20}{:<8}{:<15}{:<20}{:<8}{:<15}'
  print(fmt.format('most played champs','# games','most banned champs','# games','highest wr champs','% wr','# games','lowest wr champs','% wr','# games'))
  messages = [fmt.format('most played champs','# games','most banned champs','# games','highest wr champs','% wr','# games','lowest wr champs','% wr','# games')]
  for _, (mp, mb, hw, lw) in enumerate(zip(most_played,most_banned,highest_wr,lowest_wr)):
    print(fmt.format(*mp,*mb,*hw,*lw))
    messages.append(fmt.format(*mp,*mb,*hw,*lw))
  return messages

def show_player_wr_by_champ(matches,name='TensorFlow'):
  if name != '':
    player = [(x[y]['champ'],x[y]['win']) for x in matches['player_stats'] for y in list(x) if y==name]
    champ_wr = [(c,player.count((c,True))/(player.count((c,True))+player.count((c,False))),collections.Counter([x[0] for x in player])[c]) for c in np.unique([x[0] for x in player])]
    champ_wr.sort(key=lambda x: x[-1], reverse=True)
    print('\n'+name)
    messages = [name+"'s winrates"]
    [print('{}: {:.2f}% {} games'.format(x,y*100,z)) for x,y,z in champ_wr]
    [messages.append('{}: {:.2f}% {} games'.format(x,y*100,z)) for x,y,z in champ_wr]
    print('\n'+str(len(champ_wr))+' unique champs played')
    messages.append('\n'+str(len(champ_wr))+' unique champs played')
    return messages

def plot_elo_history(ratings,name='TensorFlow',out_dir=None,fn=None):
  num_players = len(ratings)
  places = np.arange(num_players)
  key_idx = [int(np.round(np.percentile(places,x))) for x in np.linspace(0,100,7)]
  name_list = [name] + [ratings.iloc[k].name for k in key_idx]
  name_list = list(set(name_list))
  sns.set_theme(style="darkgrid")
  _, ax = plt.subplots(figsize=(20,10))
  sorted_name_list = [x for x in ratings.index if x in name_list]
  for n in sorted_name_list:
    m='o' if n==name else ''
    sns.lineplot(data=[trueskill.expose(x) for x in ratings['history'][n]],ax=ax,legend='full',label=n,marker=m)
  plt.xlabel('Game #')
  plt.ylabel('Rating')
  if out_dir is not None:
    out_fn = 'elo_history'
    if fn is not None:
      out_fn+='_'+fn
    plt.savefig(str(Path(out_dir) / (out_fn+'.png')))

def plot_rank_dist(ratings,out_dir=None,bw_method=None,type='rating'):
  plt.subplots(figsize=(20,10))
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
  if out_dir is not None:
    plt.savefig(str(Path(out_dir) / 'rank_distribution.png'))

def synergy(wins, totals_with, out_dir=None):
  wr = wins/totals_with*100
  _, ax = plt.subplots(1,2,figsize=(30,15))
  vmax = totals_with.where(~np.triu(np.ones(totals_with.shape)).astype(bool)).max().max()
  sns.heatmap(totals_with,ax=ax[0],cmap='bwr',vmin=0,vmax=vmax,annot=True, fmt=".0f")
  ax[0].set_title('games played with')
  normalized_wr = wr.subtract(np.diagonal(wr),axis=0)
  sns.heatmap(normalized_wr,ax = ax[1],cmap='bwr',center=0,vmin=normalized_wr.min().min(),vmax=normalized_wr.max().max(),annot=wr, fmt=".0f")
  ax[1].set_title('synergy (winrate)')
  if out_dir is not None:
    plt.savefig(str(Path(out_dir)  / 'synergy.png'))

def kryptonite(wins, totals_with, losses, totals_against, out_dir=None):
  wr = wins/totals_with*100
  avg_lr = 100-np.diagonal(wr)
  lr = losses/totals_against*100
  normalized_lr = lr.subtract(avg_lr,axis=1)
  _, ax = plt.subplots(1,2,figsize=(30,15))
  vmax = totals_against.where(~np.triu(np.ones(totals_against.shape)).astype(bool)).max().max()
  sns.heatmap(totals_against,ax=ax[0],cmap='bwr',vmin=0,vmax=vmax,annot=True, fmt=".0f")
  ax[0].set_title('games played against')
  #sns.heatmap(lr.T,ax = ax[1],cmap='bwr',vmin=0,vmax=100,annot=True, fmt=".0f")
  sns.heatmap(normalized_lr.T,ax = ax[1],cmap='bwr',center=0,vmin=normalized_lr.T.min().min(),vmax=normalized_lr.T.max().max(),annot=lr.T, fmt=".0f")
  ax[1].set_title('kryptonite (lossrate)')
  if out_dir is not None:
    plt.savefig(str(Path(out_dir)  / 'kryptonite.png'))

def output_plots(matches, ratings, wins, losses, totals_with, totals_against, out_dir):
  plot_elo_history(ratings,out_dir=out_dir)
  plot_rank_dist(ratings,out_dir=out_dir)
  synergy(wins, totals_with, out_dir)
  kryptonite(wins, totals_with, losses, totals_against, out_dir)
  draft_messages = show_draft_stats(matches,num_shown=10,min_games=7)
  return draft_messages

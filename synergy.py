def synergy(wins, totals_with):
  wr = wins/totals_with*100
  fig,ax = plt.subplots(1,2,figsize=(30,15))
  vmax = totals_with.where(~np.triu(np.ones(totals_with.shape)).astype(bool)).max().max()
  sns.heatmap(totals_with,ax=ax[0],cmap='bwr',vmin=0,vmax=vmax,annot=True, fmt=".0f")
  ax[0].set_title('games played with')
  normalized_wr = wr.subtract(np.diagonal(wr),axis=0)
  sns.heatmap(normalized_wr,ax = ax[1],cmap='bwr',center=0,vmin=normalized_wr.min().min(),vmax=normalized_wr.max().max(),annot=wr, fmt=".0f")
  ax[1].set_title('synergy (winrate)')

def kryptonite(wins, totals_with, losses, totals_against):
  wr = wins/totals_with*100
  avg_lr = 100-np.diagonal(wr)
  lr = losses/totals_against*100
  normalized_lr = lr.subtract(avg_lr,axis=1)
  fig,ax = plt.subplots(1,2,figsize=(30,15))
  vmax = totals_against.where(~np.triu(np.ones(totals_against.shape)).astype(bool)).max().max()
  sns.heatmap(totals_against,ax=ax[0],cmap='bwr',vmin=0,vmax=vmax,annot=True, fmt=".0f")
  ax[0].set_title('games played against')
  #sns.heatmap(lr.T,ax = ax[1],cmap='bwr',vmin=0,vmax=100,annot=True, fmt=".0f")
  sns.heatmap(normalized_lr.T,ax = ax[1],cmap='bwr',center=0,vmin=normalized_lr.T.min().min(),vmax=normalized_lr.T.max().max(),annot=lr.T, fmt=".0f")
  ax[1].set_title('kryptonite (lossrate)')
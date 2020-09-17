"""
PULL HOUSING START, POPULATION DATA, AND HOUSE PRICES

https://www.sfu.ca/mpp/faculty-associates/josh-gordon/selected-publications.html
https://www.theglobeandmail.com/opinion/article-the-supply-crisis-in-canadas-housing-market-isnt-backed-up-by-the/

"""

import os
import pandas as pd
import numpy as np
from plotnine import *

# Calculate the population adjusted housing starts

# Load population
tmp1 = pd.read_csv('pop_2000.csv', nrows=47, header=None)
tmp1 = pd.DataFrame(tmp1.iloc[:,1:].T.values,columns=tmp1.iloc[:,0])
tmp2 = pd.read_csv('pop_2001.csv', nrows=47, header=None)
tmp2 = pd.DataFrame(tmp2.iloc[:,1:].T.values,columns=tmp2.iloc[:,0])
tmp1.columns = [z[0] for z in tmp1.columns.str.replace('[^A-Za-z\\,\\s\\-]','').str.split('\\,\\s')]
tmp2.columns = [z[0] for z in tmp2.columns.str.replace('[^A-Za-z\\,\\s\\-]','').str.split('\\,\\s')]
assert tmp1.columns.isin(tmp2.columns).all()
tmp1.Date = pd.to_datetime(tmp1.Date,format='%b-%y')
tmp2.Date = pd.to_datetime(tmp2.Date,format='%y-%b')
df_pop = pd.concat([tmp1, tmp2]).melt('Date',None,'geo')
df_pop.value = df_pop.value.str.replace('\\,','').astype(float)
df_pop = df_pop[df_pop.geo.isin(['Vancouver','Toronto'])].reset_index(None,True)
df_pop = df_pop.assign(year=lambda x: x.Date.dt.year).groupby(['geo','year']).value.mean().reset_index()

# Load housing starts
tmp1 = pd.read_csv('starts_toronto.csv',nrows=360).assign(geo='Toronto')
tmp2 = pd.read_csv('starts_vancouver.csv',nrows=360).assign(geo='Vancouver')
df_starts = pd.concat([tmp1, tmp2])
df_starts = df_starts[['date','All','geo']].rename(columns={'All':'starts'})
df_starts.starts = df_starts.starts.str.replace(',','').astype(int)
dd = np.where(df_starts.date.str.contains('^[A-Z]'),df_starts.date, df_starts.date.str.split('-',1,True).iloc[:,[1,0]].apply(lambda x: '-'.join(x),1))
df_starts.date = pd.to_datetime(dd, format='%b-%y')
df_starts = df_starts.assign(year=lambda x: x.date.dt.year).groupby(['geo','year']).starts.sum().reset_index()

# Merge
df_both = df_pop.merge(df_starts).assign(rel = lambda x: x.starts / x.value)
df_both = df_both.melt(['geo','year'],['starts','rel'],'metric','val')
df_res = df_both.assign(half=lambda x: np.where(x.year <= 2009,'<2010','>2010')).groupby(['geo','metric','half']).val.mean().reset_index()
df_res = df_res.pivot_table('val',['geo','metric'],'half').reset_index()
print(df_res.assign(ratio=lambda x: x['>2010']/x['<2010']-1))

# Make a plot
tit = 'Trend in housing starts between Vancouver/Toronto CMA\nAll building types'
di_metric = {'starts':'Starts', 'rel':'Starts / population'}
gg_starts = (ggplot(df_both, aes(x='year', y='val', color='geo')) +
             theme_bw() + geom_line() + ggtitle(tit) + geom_point() +
             labs(x='Year',y='(adjusted) Starts') +
             facet_wrap('~metric',labeller=labeller(metric=di_metric),scales='free_y') +
             scale_color_discrete(name='City') +
             geom_vline(xintercept=2010,linetype='--') +
             theme(subplots_adjust={'wspace': 0.25}))
gg_starts.save('gg_starts.png',width=12,height=5)


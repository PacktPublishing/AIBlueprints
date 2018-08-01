
import numpy as np
import pandas as pd
import scipy.stats
import dateutil
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt

orig_pageviews = pd.read_csv('wikipedia_mainpage.csv', parse_dates=[0], index_col=[0])

chunksize = 30 # one month

# plot various zscore thresholds
f, axarr = plt.subplots(2, 2)
col = 0
row = 0
for zscore_threshold in [0.5, 1.0, 1.5, 2.0]:
    pageviews = orig_pageviews.copy()
    pageviews['Anomalous'] = False
    chunk = pageviews.ix[:chunksize]['Views']

    for i in range(1, len(pageviews)-chunksize):
        zscores = np.absolute(scipy.stats.zscore(chunk))
        #print(chunk, zscores)
        
        # check if most recent value is anomalous
        if zscores[-1] > zscore_threshold:
            #print(pageviews.index[i+chunksize-2])
            pageviews.at[pageviews.index[i+chunksize-2], 'Anomalous'] = True

        # drop oldest value, add new value
        chunk = pageviews.ix[i:i+chunksize]['Views']
    #print(pageviews)

    axarr[row, col].plot(pageviews.ix[~pageviews['Anomalous']].index,
                         pageviews.ix[~pageviews['Anomalous']]['Views'], color='gray', linewidth=1, zorder=1)
    axarr[row, col].scatter(pageviews.ix[pageviews['Anomalous']].index,
                            pageviews.ix[pageviews['Anomalous']]['Views'], color='red', s=2, zorder=2)
    axarr[row, col].set_title('zscore threshold = %.2f' % zscore_threshold)
    axarr[row, col].axes.get_xaxis().set_visible(False)
    axarr[row, col].axes.get_yaxis().set_visible(False)
    col += 1
    if col == 2:
        col = 0
        row += 1

f.set_size_inches(10, 6)
plt.savefig('wikipedia-moving-outliers.png', dpi=300, bbox_inches='tight', pad_inches=0)


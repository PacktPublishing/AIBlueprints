
import numpy as np
import pandas as pd
import scipy.stats
import dateutil
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt

pageviews = pd.read_csv('wikipedia_mainpage.csv', parse_dates=[0], index_col=[0])

print(pageviews)

zscores = np.absolute(scipy.stats.zscore(pageviews['Views']))

print(zscores)

# plot various zscore thresholds
f, axarr = plt.subplots(2, 2)
col = 0
row = 0
for zscore_threshold in [0.5, 1.0, 1.5, 2.0]:
    axarr[row, col].plot(pageviews.ix[zscores < zscore_threshold].index,
                         pageviews.ix[zscores < zscore_threshold]['Views'], color='gray', linewidth=1)
    axarr[row, col].scatter(pageviews.ix[zscores >= zscore_threshold].index,
                            pageviews.ix[zscores >= zscore_threshold]['Views'], color='red', s=2)
    axarr[row, col].set_title('zscore threshold = %.2f' % zscore_threshold)
    axarr[row, col].axes.get_xaxis().set_visible(False)
    axarr[row, col].axes.get_yaxis().set_visible(False)
    col += 1
    if col == 2:
        col = 0
        row += 1

f.set_size_inches(10, 6)
plt.savefig('wikipedia-outliers.png', dpi=300, bbox_inches='tight', pad_inches=0)



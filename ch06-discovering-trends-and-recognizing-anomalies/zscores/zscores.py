
import numpy as np
import pandas as pd
import scipy.stats
import dateutil
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt

times = pd.read_csv('proctime.csv.zip', header=None, names=['date', 'proctime'],
                    parse_dates=[0], index_col=[0],
                    date_parser = lambda d: dateutil.parser.parse(d, yearfirst=True))

print(times)

zscores = scipy.stats.zscore(times['proctime'])

print(zscores)

plt.scatter(times.ix[zscores < 5.0].index.astype(np.int64),
            times.ix[zscores < 5.0]['proctime'], color='gray', s=1)
plt.scatter(times.ix[zscores >= 5.0].index.astype(np.int64),
            times.ix[zscores >= 5.0]['proctime'], color='red', s=2)

plt.xticks(())
plt.yticks(())

plt.savefig('outliers.png', dpi=300, bbox_inches='tight', pad_inches=0)


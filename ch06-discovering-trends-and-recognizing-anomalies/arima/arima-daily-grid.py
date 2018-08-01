import pandas as pd
from sklearn.metrics import mean_squared_error
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt
 
series = pd.read_csv('daily-users.csv', header=0, parse_dates=[0], index_col=0, squeeze=True)

from statsmodels.tsa.arima_model import ARIMA
f, axarr = plt.subplots(2, 2)
col = 0
row = 0
for pdq in [(3,0,0), (0,0,3), (3,1,0), (3,1,1)]:
    print(pdq)
    axarr[row, col].set_title('p = %d, d = %d, q = %d' % pdq)
    model = ARIMA(series.ix[:'2017-12-31'], pdq, freq='D').fit()
    predictions, _, _ = model.forecast(len(series.ix['2018-01-01':]))
    print(predictions)
    print(series.ix['2018-01-01':][:len(predictions)])
    print("Mean squared error: %.2f"
          % mean_squared_error(series.ix['2018-01-01':][:len(predictions)], predictions))

    series.ix['2017-01-01':].plot(color='gray', linewidth=1, ax=axarr[row, col])
    pred_series = pd.Series(predictions, index=series.ix['2018-01-01':][:len(predictions)].index)
    pred_series.plot(color='blue', linewidth=3, ax=axarr[row, col])
    axarr[row, col].axes.get_xaxis().set_visible(False)
    axarr[row, col].axes.get_yaxis().set_visible(False)

    col += 1
    if col == 2:
        col = 0
        row += 1

plt.savefig('arima-daily-grid.png', dpi=300, bbox_inches='tight', pad_inches=0)


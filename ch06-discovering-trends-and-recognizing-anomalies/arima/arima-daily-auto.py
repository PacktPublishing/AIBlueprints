import pandas as pd
from sklearn.metrics import mean_squared_error
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt
 
series = pd.read_csv('daily-users.csv', header=0, parse_dates=[0], index_col=0, squeeze=True)

from statsmodels.tsa.arima_model import ARIMA
from pyramid.arima import auto_arima
stepwise_model = auto_arima(series.ix[:'2017-12-31'],
                            start_p=1, start_q=1,
                            max_p=5, max_q=5, m=7,
                            start_P=0, seasonal=True,
                            trace=True, error_action='ignore',  
                            suppress_warnings=True, stepwise=True)
print(stepwise_model.aic())
print(stepwise_model.params())
print(stepwise_model.summary())

stepwise_model.fit(series.ix[:'2017-12-31'])
predictions = stepwise_model.predict(n_periods=len(series.ix['2018-01-01':]))
print(predictions)
print(series.ix['2018-01-01':][:len(predictions)])
print("Mean squared error: %.2f"
      % mean_squared_error(series.ix['2018-01-01':][:len(predictions)], predictions))

series.ix['2017-01-01':].plot(color='gray', linewidth=1)
pred_series = pd.Series(predictions, index=series.ix['2018-01-01':][:len(predictions)].index)
pred_series.plot(color='blue', linewidth=1)

plt.savefig('arima-daily-auto-predictions.png', dpi=300, bbox_inches='tight', pad_inches=0)


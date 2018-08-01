import pandas as pd
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

series = pd.read_csv('daily-users.csv', header=0, parse_dates=[0], index_col=0, squeeze=True)

from pydlm import dlm, trend, seasonality, longSeason

constant = trend(degree=0, name="constant")
seasonal_week = seasonality(period=7, name='seasonal_week')
model = dlm(series.ix['2015-01-01':'2017-12-31']) + constant + seasonal_week

model.fit()

model.turnOff('data points')
model.turnOff('confidence interval')
model.plot()
plt.savefig('bayesian-daily.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

print(model.getMSE())

model.turnOff('predict plot')
model.turnOff('filtered plot')
model.plot('constant')
plt.savefig('bayesian-daily-constant.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()
model.plot('seasonal_week')
plt.savefig('bayesian-daily-seasonal-week.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

predictions, conf = model.predictN(N=168)
print(predictions)
print(conf)

print("Mean squared error: %.2f"
      % mean_squared_error(series.ix['2018-01-01':][:len(predictions)], predictions))

series.ix['2017-01-01':].plot(color='gray', linewidth=1)
pred_series = pd.Series(predictions, index=series.ix['2018-01-01':][:len(predictions)].index)
pred_series.plot(color='blue', linewidth=1)

plt.savefig('bayesian-daily-prediction.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

## Add monthly seasonality

constant = trend(degree=0, name="constant")
seasonal_week = seasonality(period=7, name='seasonal_week')
seasonal_month = longSeason(period=12, stay=31, data=series['2015-01-01':'2017-12-31'], name='seasonal_month')
model = dlm(series.ix['2015-01-01':'2017-12-31']) + constant + seasonal_week + seasonal_month
model.tune()
model.fit()

model.turnOff('data points')
model.turnOff('confidence interval')
model.plot()
plt.savefig('bayesian-daily-with-monthly.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

print(model.getMSE())

model.turnOff('predict plot')
model.turnOff('filtered plot')
model.plot('constant')
plt.savefig('bayesian-daily-constant-with-monthly.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()
model.plot('seasonal_week')
plt.savefig('bayesian-daily-seasonal-week-with-monthly.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()
model.plot('seasonal_month')
plt.savefig('bayesian-daily-seasonal-month-with-monthly.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

predictions, conf = model.predictN(N=168)
print(predictions)
print(conf)

print("Mean squared error: %.2f"
      % mean_squared_error(series.ix['2018-01-01':][:len(predictions)], predictions))

series.ix['2017-01-01':].plot(color='gray', linewidth=1)
pred_series = pd.Series(predictions, index=series.ix['2018-01-01':][:len(predictions)].index)
pred_series.plot(color='blue', linewidth=1)

plt.savefig('bayesian-daily-prediction-with-monthly.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()


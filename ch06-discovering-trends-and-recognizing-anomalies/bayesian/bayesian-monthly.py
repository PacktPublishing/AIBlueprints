import pandas as pd
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

series = pd.read_csv('daily-users.csv', header=0, parse_dates=[0], index_col=0, squeeze=True)

# group daily counts into monthly
series = series.groupby(pd.Grouper(freq='M')).sum()

from pydlm import dlm, trend, seasonality, longSeason

constant = trend(degree=0, name="constant")
seasonal_month = seasonality(period=12, name='seasonal_month')
model = dlm(series.ix['2015-01-01':'2016-12-31']) + constant + seasonal_month

model.tune()
model.fit()

model.turnOff('data points')
model.turnOff('confidence interval')
model.plot()
plt.savefig('bayesian-monthly.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

print(model.getMSE())

model.turnOff('predict plot')
model.turnOff('filtered plot')
model.plot('constant')
plt.savefig('bayesian-monthly-constant.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()
model.plot('seasonal_month')
plt.savefig('bayesian-monthly-seasonal-month.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

predictions, conf = model.predictN(N=18)
print(predictions)
print(conf)

print("Mean squared error: %.2f"
      % mean_squared_error(series.ix['2017-01-01':][:len(predictions)], predictions))

series.plot(color='gray', linewidth=1)
pred_series = pd.Series(predictions, index=series.ix['2017-01-01':][:len(predictions)].index)
pred_series.plot(color='blue', linewidth=1)

plt.savefig('bayesian-monthly-prediction.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()


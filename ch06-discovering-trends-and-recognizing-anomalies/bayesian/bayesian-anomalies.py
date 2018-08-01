import math
import pandas as pd
import scipy.stats

series = pd.read_csv('daily-users.csv', header=0, parse_dates=[0], index_col=0, squeeze=True)

# Use just last 90 days
series = series.ix[-90:]

from pydlm import dlm, trend, seasonality

constant = trend(degree=0, name="constant")
seasonal_week = seasonality(period=7, name='seasonal_week')
model = dlm(series) + constant + seasonal_week
model.tune()
model.fit()

# Forecast one day
predictions, conf = model.predictN(N=1)
print("Prediction for next day: %.2f, confidence: %s" % (predictions[0], conf[0]))

while True:
    actual = float(input("Actual value? "))
    zscore = (actual - predictions[0]) / math.sqrt(conf[0])
    print("Z-score: %.2f" % zscore)
    pvalue = scipy.stats.norm.sf(abs(zscore))*2
    print("p-value: %.2f" % pvalue)


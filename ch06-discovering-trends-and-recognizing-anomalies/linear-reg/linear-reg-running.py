
import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt

msgs = pd.read_csv('r-help.csv.zip', usecols=[0,3], parse_dates=[1], index_col=[1])

msgs_daily_cnts = msgs.resample('D').count()
msgs_daily_cnts['date_delta'] = (msgs_daily_cnts.index - msgs_daily_cnts.index.min()) / np.timedelta64(1,'D')
msgs_daily_cnts.sort_values(by=['date_delta'])

for chunk in range(1000, len(msgs_daily_cnts.index)-1000, 500):
    train = msgs_daily_cnts[chunk-1000:chunk]
    train_X = train['date_delta'].values.reshape((-1,1))
    train_y = train['Message-ID']

    test = msgs_daily_cnts[chunk:chunk+1000]
    test_X = test['date_delta'].values.reshape((-1,1))
    test_y = test['Message-ID']

    reg = linear_model.LinearRegression()
    reg.fit(train_X, train_y)
    print('Coefficients: \n', reg.coef_)

    predicted_cnts = reg.predict(test_X)

    # The mean squared error
    print("Mean squared error: %.2f"
          % mean_squared_error(test_y, predicted_cnts))
    # Explained variance score: 1 is perfect prediction
    print('Variance score: %.2f' % r2_score(test_y, predicted_cnts))

    plt.scatter(train_X, train_y, color='gray', s=1)
    plt.scatter(test_X, test_y, color='gray', s=1)
    plt.plot(test_X, predicted_cnts, color='blue', linewidth=5)

plt.xticks(())
plt.yticks(())

plt.savefig('linear-reg-running.png', dpi=300, bbox_inches='tight', pad_inches=0)


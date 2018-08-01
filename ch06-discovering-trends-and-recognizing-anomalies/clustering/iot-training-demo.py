
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_distances

benign_traffic_orig = pd.read_csv('benign_traffic.csv.zip', nrows=2000)
gafgyt_traffic = pd.read_csv('gafgyt_traffic.csv.zip', nrows=2000)

for n in [0, 500, 1000, 1500, 2000]:
    benign_traffic = pd.concat([benign_traffic_orig.copy(), gafgyt_traffic[:n]], axis=0)

    # Define the "average" benign traffic
    benign_avg = np.median(benign_traffic.values, axis=0, keepdims=True)

    # Compute distances to this avg
    benign_avg_benign_dists = cosine_distances(benign_avg, benign_traffic_orig)

    threshold = 0.90

    benign_avg_gafgyt_dists = cosine_distances(benign_avg, gafgyt_traffic)

    fp = np.shape(benign_avg_benign_dists[np.where(benign_avg_benign_dists >= threshold)])[0]
    tn = np.shape(benign_avg_benign_dists[np.where(benign_avg_benign_dists < threshold)])[0]
    tp = np.shape(benign_avg_gafgyt_dists[np.where(benign_avg_gafgyt_dists >= threshold)])[0]
    fn = np.shape(benign_avg_gafgyt_dists[np.where(benign_avg_gafgyt_dists < threshold)])[0]

    print("Bad data: %-5d\ttp = %-5d  fp = %-5d  tn = %-5d  fn = %-5d" % (n, tp, fp, tn, fn))


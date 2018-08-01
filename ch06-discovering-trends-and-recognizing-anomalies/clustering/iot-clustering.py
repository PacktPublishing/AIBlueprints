
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') # for saving figures
import matplotlib.pyplot as plt

benign_traffic = pd.read_csv('benign_traffic.csv.zip')
gafgyt_traffic = pd.read_csv('gafgyt_traffic.csv.zip', nrows=2000)

print("Benign traffic:")
print(benign_traffic.head())
print("Gafgyt traffic:")
print(gafgyt_traffic.head())

# Compute distances from every benign data point to every other
from sklearn.metrics.pairwise import cosine_distances
benign_dists = cosine_distances(benign_traffic)
print("Benign self-distances:")
print(benign_dists)
print(np.shape(benign_dists))
print("Min, max:", np.min(benign_dists), np.max(benign_dists))
print("Mean:", np.mean(benign_dists))
print("Median:", np.median(benign_dists))

# Mix in gafgyt attack records, then plot again
# (we'll append them at the end so we can keep track
# of which rows are gafgyt and which are benign)

mixed_traffic = np.vstack((benign_traffic, gafgyt_traffic))

mixed_dists = cosine_distances(mixed_traffic)
print("Mixed self-distances:")
print(mixed_dists)
print(np.shape(mixed_dists))
print("Min, max:", np.min(mixed_dists), np.max(mixed_dists))
print("Mean:", np.mean(mixed_dists))
print("Median:", np.median(mixed_dists))

from sklearn.decomposition import PCA
clf = PCA(n_components=2)
pos = clf.fit_transform(mixed_dists)
print(pos)
print(np.shape(pos))

gafgyt_cnt = len(gafgyt_traffic)
plt.scatter(pos[:-gafgyt_cnt, 0], pos[:-gafgyt_cnt, 1], s=1, color='silver')
plt.scatter(pos[-gafgyt_cnt:, 0], pos[-gafgyt_cnt:, 1], s=20, color='blue')
plt.axis('off')
plt.savefig('mixed-similarity.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.close()

# Find average cosine distance between benign and gafgyt attack records
benign_gafgyt_dists = cosine_distances(benign_traffic, gafgyt_traffic)
print("Benign vs. Gafgyt distances:")
print(np.shape(benign_gafgyt_dists))
print(benign_gafgyt_dists)
print("Min, max:", np.min(benign_gafgyt_dists), np.max(benign_gafgyt_dists))
print("Mean:", np.mean(benign_gafgyt_dists))
print("Median:", np.median(benign_gafgyt_dists))

# Find average cosine distance between gafgyt attack records and themselves
gafgyt_dists = cosine_distances(gafgyt_traffic)
print("Gafgyt self-distances:")
print(np.shape(gafgyt_dists))
print(gafgyt_dists)
print("Min, max:", np.min(gafgyt_dists), np.max(gafgyt_dists))
print("Mean:", np.mean(gafgyt_dists))
print("Median:", np.median(gafgyt_dists))

# Define the "average" benign traffic
benign_avg = np.median(benign_traffic.values, axis=0, keepdims=True)
print(benign_avg)

# Compute distances to this avg
benign_avg_benign_dists = cosine_distances(benign_avg, benign_traffic)
print("Distances of benign traffic to benign_avg:")
print(benign_avg_benign_dists)
print(np.shape(benign_avg_benign_dists))
print(benign_avg_benign_dists)
print("Min, max:", np.min(benign_avg_benign_dists), np.max(benign_avg_benign_dists))
print("Mean:", np.mean(benign_avg_benign_dists))
print("Median:", np.median(benign_avg_benign_dists))

# Choose a threshold to label anomalous traffic
#
# Let's count how many benign records are >= threshold, and how many gafgyt are >= threshold
threshold = 0.99

benign_avg_gafgyt_dists = cosine_distances(benign_avg, gafgyt_traffic)
print("Distances of gafgyt traffic to benign_avg:")
print(benign_avg_gafgyt_dists)
print(np.shape(benign_avg_gafgyt_dists))
print(benign_avg_gafgyt_dists)
print("Min, max:", np.min(benign_avg_gafgyt_dists), np.max(benign_avg_gafgyt_dists))
print("Mean:", np.mean(benign_avg_gafgyt_dists))
print("Median:", np.median(benign_avg_gafgyt_dists))

print("Benign >= threshold:")
print(np.shape(benign_avg_benign_dists[np.where(benign_avg_benign_dists >= threshold)]))
print("Benign < threshold:")
print(np.shape(benign_avg_benign_dists[np.where(benign_avg_benign_dists < threshold)]))

print("Gafgyt vs. benign >= threshold:")
print(np.shape(benign_avg_gafgyt_dists[np.where(benign_avg_gafgyt_dists >= threshold)]))
print("Gafgyt vs. benign < threshold:")
print(np.shape(benign_avg_gafgyt_dists[np.where(benign_avg_gafgyt_dists < threshold)]))

# Final test, new attack data

mirai_traffic = pd.read_csv('mirai_udp.csv.zip', nrows=2000) #, usecols=cols)

benign_avg_mirai_dists = cosine_distances(benign_avg, mirai_traffic)
print("Distances of mirai traffic to benign_avg:")
print(benign_avg_mirai_dists)
print(np.shape(benign_avg_mirai_dists))
print(benign_avg_mirai_dists)
print("Min, max:", np.min(benign_avg_mirai_dists), np.max(benign_avg_mirai_dists))
print("Mean:", np.mean(benign_avg_mirai_dists))
print("Median:", np.median(benign_avg_mirai_dists))

print("Mirai vs. benign >= threshold:")
print(np.shape(benign_avg_mirai_dists[np.where(benign_avg_mirai_dists >= threshold)]))
print("Mirai vs. benign < threshold:")
print(np.shape(benign_avg_mirai_dists[np.where(benign_avg_mirai_dists < threshold)]))


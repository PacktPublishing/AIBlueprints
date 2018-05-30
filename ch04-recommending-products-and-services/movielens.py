"""
An experiment based off the MovieLens 20M dataset, based off
https://github.com/benfred/implicit/blob/master/examples/movielens.py

This code will automatically download a HDF5 version of this
dataset when first run. The original dataset can be found here:
https://grouplens.org/datasets/movielens/.

Since this dataset contains explicit 5-star ratings, the ratings are
filtered down to positive reviews (3+ stars) to construct an implicit
dataset
"""

import time
import numpy as np
from scipy.sparse import coo_matrix

from implicit.approximate_als import FaissAlternatingLeastSquares
from implicit.nearest_neighbours import bm25_weight
from implicit.datasets.movielens import get_movielens

def experiment(B, K1, conf, variant='20m', min_rating=3.0):
    # read in the input data file
    _, ratings = get_movielens(variant)
    ratings = ratings.tocsr()

    # remove things < min_rating, and convert to implicit dataset
    # by considering ratings as a binary preference only
    ratings.data[ratings.data < min_rating] = 0
    ratings.eliminate_zeros()
    ratings.data = np.ones(len(ratings.data))

    training = ratings.tolil() # makes a copy

    # remove some implicit ratings (make them zeros, i.e., missing)
    # (these ratings might have already been missing, in fact)
    movieids = np.random.randint(low=0, high=np.shape(ratings)[0], size=100000)
    userids = np.random.randint(low=0, high=np.shape(ratings)[1], size=100000)
    training[movieids, userids] = 0

    model = FaissAlternatingLeastSquares(factors=128, iterations=30)
    model.approximate_recommend = False
    model.approximate_similar_items = False
    model.show_progress = False

    # possibly recalculate scores by bm25weight.
    if B != "NA":
        training = bm25_weight(training, B=B, K1=K1).tocsr()

    # train the model
    model.fit(training)

    # compute the predicted ratings
    moviescores = np.einsum('ij,ij->i', model.item_factors[movieids], model.user_factors[userids])
    # using confidence threshold, find boolean predictions
    preds = (moviescores >= conf)
    true_ratings = np.ravel(ratings[movieids,userids])
    # both model predicted True and user rated movie
    tp = true_ratings[preds].sum()
    #tp = ratings[:,userids][preds][movieids].sum()
    # model predicted True but user did not rate movie
    fp = preds.sum() - tp
    # model predicted False but user did rate movie
    fn = true_ratings.sum() - tp
    if tp+fp == 0:
        prec = float('nan')
    else:
        prec = float(tp)/float(tp+fp)
    if tp+fn == 0:
        recall = float('nan')
    else:
        recall = float(tp)/float(tp+fn)
    if B != "NA":
        print("%.2f,%.2f,%.2f,%d,%d,%d,%.2f,%.2f" % (B, K1, conf, tp, fp, fn, prec, recall))
    else:
        print("NA,NA,%.2f,%d,%d,%d,%.2f,%.2f" % (conf, tp, fp, fn, prec, recall))

print("B,K1,Confidence,TP,FP,FN,Precision,Recall")
confidences = [0.0, 0.2, 0.4, 0.6, 0.8]
for iteration in range(5):
    seed = int(time.time())
    for conf in confidences:
        np.random.seed(seed)
        experiment(0.0, 0.0, conf)
    for conf in confidences:
        np.random.seed(seed)
        experiment("NA", "NA", conf)
    for B in [0.25, 0.50, 0.75, 1.0]:
        for K1 in [1.0, 3.0]:
            for conf in confidences:
                np.random.seed(seed)
                experiment(B, K1, conf)


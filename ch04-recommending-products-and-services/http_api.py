from flask import Flask, abort
from flask import request
import atexit
import pickle
import time
import pandas as pd
import numpy as np
import re
import threading
import json
from pathlib import Path
from scipy.sparse import coo_matrix, csr_matrix
from implicit.nearest_neighbours import bm25_weight

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Choose first import if faiss is not installed:
from implicit.als import AlternatingLeastSquares
from implicit.approximate_als import FaissAlternatingLeastSquares

app = Flask(__name__)

model = None
model_lock = threading.Lock()
purchases = {}
purchases_pickle = Path('purchases.pkl')
userids = []
userids_reverse = {}
usernames = {}
productids = []
productids_reverse = []
productnames = {}
purchases_matrix = None
purchases_matrix_T = None
stats = {'purchase_count': 0, 'user_rec': 0}

def fit_model():
    global model, userids, userids_reverse, productids, productids_reverse, purchases_matrix, purchases_matrix_T
    with model_lock:
        app.logger.info("Fitting model...")
        start = time.time()
        with open(purchases_pickle, 'wb') as f:
            pickle.dump((purchases, usernames, userids, userids_reverse, productnames, productids, productids_reverse), f)

        # choose first line if faiss is not installed
        #model = AlternatingLeastSquares(factors=64, dtype=np.float32)
        model = FaissAlternatingLeastSquares(factors=128, dtype=np.float32, iterations=30)

        model.approximate_recommend = False
        model.approximate_similar_items = False
        data = {'userid': [], 'productid': [], 'purchase_count': []}
        for userid in purchases:
            for productid in purchases[userid]:
                data['userid'].append(userid)
                data['productid'].append(productid)
                data['purchase_count'].append(purchases[userid][productid])
        app.logger.info("Gathered %d data points in %0.2fs" % (len(data['purchase_count']), time.time() - start))
        start = time.time()
        df = pd.DataFrame(data)
        df['userid'] = df['userid'].astype("category")
        df['productid'] = df['productid'].astype("category")
        userids = list(df['userid'].cat.categories)
        userids_reverse = dict(zip(userids, list(range(len(userids)))))
        productids = list(df['productid'].cat.categories)
        productids_reverse = dict(zip(productids, list(range(len(productids)))))
        purchases_matrix = coo_matrix((df['purchase_count'].astype(np.float32),
                                       (df['productid'].cat.codes.copy(),
                                        df['userid'].cat.codes.copy())))
        print("Matrix shape: %s, max value: %.2f" % (np.shape(purchases_matrix), np.max(purchases_matrix)))
        app.logger.info("Matrix shape: %s, max value: %.2f" % (np.shape(purchases_matrix), np.max(purchases_matrix)))
        app.logger.info("Built matrix in %0.2fs" % (time.time() - start))
        start = time.time()
        purchases_matrix = bm25_weight(purchases_matrix, K1=2.0, B=0.25)
        purchases_matrix_T = purchases_matrix.T.tocsr()
        app.logger.info("BM25 weighted matrix in %0.2fs" % (time.time() - start))
        start = time.time()
        purchases_matrix = purchases_matrix.tocsr() # to support indexing in recommend/similar_items functions
        app.logger.info("Converted to CSR matrix in %0.2fs" % (time.time() - start))
        start = time.time()
        model.fit(purchases_matrix)
        app.logger.info("Fitted model in %0.2fs" % (time.time() - start))

@app.route('/purchased', methods=['POST'])
def purchased():
    global purchases, usernames, productnames, stats
    userid = request.form['userid'].strip()
    username = request.form['username'].strip()
    productid = request.form['productid'].strip()
    productname = request.form['productname'].strip()
    #app.logger.info("Recording purchase: user %s (%s) bought product %s (%s)" % (username, userid, productname, productid))
    with model_lock:
        usernames[userid] = username
        productnames[productid] = productname
        if userid not in purchases:
            purchases[userid] = {}
        if productid not in purchases[userid]:
            purchases[userid][productid] = 0
        purchases[userid][productid] += 1

        # check if we know this user and product already and could have recommended this product
        if model is not None and userid in userids_reverse and productid in productids_reverse:
            # check if we have enough history for this user to bother with recommendations
            user_purchase_count = 0
            for productid in purchases[userid]:
                user_purchase_count += purchases[userid][productid]
            if user_purchase_count >= 10:
                # keep track if we ever compute a confident recommendation
                confident = False
                # check if this product was recommended as a user-specific recommendation
                print(username, userid, userids_reverse[userid])
                for prodidx, score in model.recommend(userids_reverse[userid], purchases_matrix_T, N=10):
                    if score >= 0.5:
                        confident = True
                        print("%d -- %.2f -- %s -- %s" % (prodidx, score, productnames[productids[prodidx]], productname))
                        if productids[prodidx] == productid:
                            stats['user_rec'] += 1
                            break
                if confident:
                    stats['purchase_count'] += 1
                    print(userid, productid, user_purchase_count, confident, stats['purchase_count'], stats['user_rec'])
    return 'OK\n'

@app.route('/stats', methods=['GET'])
def show_stats():
    tmpstats = dict(stats)
    tmpstats['users'] = len(userids)
    tmpstats['products'] = len(productids)
    return json.dumps(tmpstats)

@app.route('/dump-factors', methods=['GET'])
def dump_factors():
    numfactors = int(request.args['numfactors'].strip())
    model = AlternatingLeastSquares(factors=numfactors, dtype=np.float32, use_gpu=False, iterations=30)
    model.approximate_recommend = False
    model.approximate_similar_items = False
    data = {'userid': [], 'productid': [], 'purchase_count': []}
    for userid in purchases:
        for productid in purchases[userid]:
            data['userid'].append(userid)
            data['productid'].append(productid)
            data['purchase_count'].append(purchases[userid][productid])
    df = pd.DataFrame(data)
    df['userid'] = df['userid'].astype("category")
    df['productid'] = df['productid'].astype("category")
    userids = list(df['userid'].cat.categories)
    userids_reverse = dict(zip(userids, list(range(len(userids)))))
    productids = list(df['productid'].cat.categories)
    productids_reverse = dict(zip(productids, list(range(len(productids)))))
    purchases_matrix = coo_matrix((df['purchase_count'].astype(np.float32),
                                   (df['productid'].cat.codes.copy(),
                                    df['userid'].cat.codes.copy())))
    print("Matrix shape: %s, max value: %.2f" % (np.shape(purchases_matrix), np.max(purchases_matrix)))
    purchases_matrix = bm25_weight(purchases_matrix, K1=2.0, B=0.25)
    purchases_matrix_T = purchases_matrix.T.tocsr()
    purchases_matrix = purchases_matrix.tocsr() # to support indexing in recommend/similar_items functions
    model.fit(purchases_matrix)
    np.savetxt('item_factors.csv', model.item_factors, delimiter=',')
    np.savetxt('user_factors.csv', model.user_factors, delimiter=',')
    with open('item_ids.csv', 'w') as f:
        for pid in productids_reverse:
            f.write("%s,%d,%s\n" % (pid, productids_reverse[pid], re.sub(r',', ' ', productnames[pid])))
    with open('user_ids.csv', 'w') as f:
        for uid in userids_reverse:
            f.write("%s,%d,%s\n" % (uid, userids_reverse[uid], re.sub(r',', ' ', usernames[uid])))
    return 'OK\n'

@app.route('/recommend', methods=['GET'])
def recommend():
    userid = request.args['userid'].strip()
    productid = request.args['productid'].strip()
    if model is None or userid not in usernames or productid not in productnames:
        abort(500)
    else:
        result = {}
        result['user-specific'] = []
        for prodidx, score in model.recommend(userids_reverse[userid], purchases_matrix_T, N=10):
            result['user-specific'].append((productnames[productids[prodidx]], productids[prodidx], float(score)))
        result['product-specific'] = []
        for prodidx, score in model.similar_items(productids_reverse[productid], 10):
            if productids[prodidx] != productid:
                result['product-specific'].append((productnames[productids[prodidx]], productids[prodidx], float(score)))
        return json.dumps(result)

@app.route('/user-purchases', methods=['GET'])
def user_purchases():
    userid = request.args['userid'].strip()
    if userid in purchases:
        result = []
        for productid in purchases[userid]:
            result.append((productid, productnames[productid], purchases[userid][productid]))
        return json.dumps(result)
    else:
        abort(500)

@app.route('/update-model', methods=['POST'])
def update_model():
    fit_model()
    return 'OK\n'

@app.before_first_request
def load_purchases_pickle():
    global purchases, usernames, userids, userids_reverse, productnames, productids, productids_reverse
    if purchases_pickle.is_file():
        with open(purchases_pickle, 'rb') as f:
            (purchases, usernames, userids, userids_reverse, productnames, productids, productids_reverse) = pickle.load(f)


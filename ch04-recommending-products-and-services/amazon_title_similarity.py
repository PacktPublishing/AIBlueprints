import json
import re
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
import faiss
import os.path
import pickle
import gzip

use_gpu = False

if os.path.exists('product_asin.pkl') and os.path.exists('product_text.pkl'):
    print("Loading pickled product asin's and text.")
    with open('product_asin.pkl', 'rb') as f:
        product_asin = pickle.load(f)
    with open('product_text.pkl', 'rb') as f:
        product_text = pickle.load(f)
    print("Loaded %d products" % len(product_asin))
else:
    print("Processing metadata-small.json.gz...")
    product_asin = []
    product_text = []
    with gzip.open('metadata-small.json.gz', encoding='utf-8', mode='rt') as f:
        for line in f:
            try:
                # fix improper quoting
                line = re.sub(r'(\W)\'', r'\1"', line)
                line = re.sub(r'\'(\W)', r'"\1', line)
                line = re.sub(r'(\w)"(\w)', r"\1'\2", line)
                p = json.loads(line)
                s = p['title']
                if 'description' in p:
                    s += ' ' + p['description']
                product_text.append(s)
                product_asin.append(p['asin'])
            except:
                pass
    print("Count: %d" % len(product_asin))
    with open('product_asin.pkl', 'wb') as f:
        pickle.dump(product_asin, f)
    with open('product_text.pkl', 'wb') as f:
        pickle.dump(product_text, f)

product_text = product_text[:3000000]
product_asin = product_asin[:3000000]

if os.path.exists('amazon_title_bow.npy'):
    print("Loading BOW array.")
    d = np.load('amazon_title_bow.npy')
else:
    print("Running pipeline...")
    pipeline = make_pipeline(CountVectorizer(stop_words='english', max_features=10000),
                             TfidfTransformer(),
                             TruncatedSVD(n_components=128))
    d = pipeline.fit_transform(product_text).astype('float32')
    print("Saving BOW array.")
    np.save('amazon_title_bow.npy', d)

print(d.shape)

ncols = np.shape(d)[1]
if use_gpu:
    gpu_resources = faiss.StandardGpuResources() 
    index = faiss.GpuIndexIVFFlat(gpu_resources, ncols, 400, faiss.METRIC_INNER_PRODUCT)
else:
    quantizer = faiss.IndexFlat(ncols)
    index = faiss.IndexIVFFlat(quantizer, ncols, 400, faiss.METRIC_INNER_PRODUCT)

print(index.is_trained)
index.train(d)
print(index.is_trained)
index.add(d)
print(index.ntotal)

rec_asins = ["0001048775"]

for asin in rec_asins:
    idx = -1
    for i in range(len(product_asin)):
        if product_asin[i] == asin:
            idx = i
            break
    if idx != -1:
        print('--')
        print((product_asin[idx], product_text[idx]))
        distances, indexes = index.search(d[idx:idx+1], 5)
        print(distances, indexes)
        for i in indexes[0]:
            print((product_asin[i], product_text[i]))


import os
import pandas as pd
from app import mongodb as mongodb
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Normalizer
from sklearn.pipeline import make_pipeline
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.multiclass import OneVsRestClassifier,OneVsOneClassifier
from sklearn.tree import DecisionTreeClassifier
from imblearn.ensemble import BalancedBaggingClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import confusion_matrix

import pickle


# BASE PLAYLISTS

pl_list = ['37i9dQZF1DWX83CujKHHOn', '37i9dQZF1DWT2VB7HB29Jj', '37i9dQZF1DXdZjf8WgcTKM', 
           '37i9dQZF1DWVhcOv4ieuap', '37i9dQZEVXbMfVLvbaC3bj', '37i9dQZEVXbNFJfN1Vw8d9', 
           '37i9dQZF1DWSoyxGghlqv5', '37i9dQZF1DX3NRlBOcUOcY', '37i9dQZF1DX50QitC6Oqtn', 
           '37i9dQZF1DWYqfaEyH6O9U', '37i9dQZF1DX3YSRoSdA634', '37i9dQZF1DX0BcQWzuB7ZO', 
           '37i9dQZF1DX9Dh2wgiAwVX', '37i9dQZF1DXaXB8fQg7xif', '37i9dQZEVXbMDoHDwVN2tF', 
           '37i9dQZEVXbLiRSasKsNU9', '37i9dQZF1DX0s5kDXi1oC5', '37i9dQZF1DX15JKV0q7shD', 
           '37i9dQZF1DWT34oeYRnJ0R', '37i9dQZF1DXdPec7aLTmlC', '37i9dQZF1DX6J5NfMJS675', 
           '37i9dQZF1DXcjpPPxCzYRE', '37i9dQZF1DX3ND264N08pv', '37i9dQZF1DX6ziVCJnEm59', 
           '37i9dQZF1DWZqdNJSufucb', '37i9dQZF1DX4WYpdgoIcn6', '37i9dQZF1DWV1PBrIG2weG', 
           '37i9dQZF1DWX3387IZmjNa', '37i9dQZF1DX32NsLKyzScr', '37i9dQZF1DWXCGnD7W6WDX', 
           '37i9dQZF1DXcBWIGoYBM5M','37i9dQZF1DXdo9iIZiH7LB', '37i9dQZF1DWUzaE9UzQeCb',
           '37i9dQZF1DX40F1hlCueZ7','37i9dQZF1DWYJ5kmTbkZiz','37i9dQZF1DX7tZql9TtyhL',
           '37i9dQZF1DWXpyNlpWQwux','37i9dQZF1DWYJ5kmTbkZiz','37i9dQZF1DX9oegrjMzKDW',
           '37i9dQZF1DXcz8eC5kMSWZ','37i9dQZF1DX4o1oenSJRJd','37i9dQZF1DXbTxeAdrVG2l',
           '37i9dQZF1DX4UtSsGT1Sbe', '37i9dQZF1DX8a1tdzq5tbM','37i9dQZF1DX4SBhb3fqCJd',
           '37i9dQZF1DWYmmr74INQlb','37i9dQZF1DX504r1DvyvxG','37i9dQZF1DX2TRYkJECvfC']

database = 'spotify'
db, playlists = mongodb.connectCollection(database,'playlists')

songsdb = pd.DataFrame(list(playlists.find({})))
songsdb = songsdb[songsdb['energy'].notnull()]

X = songsdb[['energy','valence','danceability']]
sns.lmplot(data=X, x='valence', y='energy',  
            fit_reg=False, legend=True, legend_out=True)

steps = [
        StandardScaler(),
         Normalizer(),
]
pipe = make_pipeline(*steps)
X = pipe.fit_transform(X)
data = pd.DataFrame(X)

data.rename(columns={
    0:'energy',
    1:'valence',
    2:'danceability'
}, inplace=True)

data['name'] = songsdb['name']
data['artist'] = songsdb['artist']
data['album'] = songsdb['album']
data['release_date'] = pd.to_datetime(songsdb.release_date, infer_datetime_format = True,errors = 'coerce')


X_2 = data[['energy','valence']]
kmeans = KMeans(n_clusters=6)
kmeans.fit(X_2)
y_kmeans = kmeans.predict(X_2)
data['label'] = y_kmeans

cluster = sns.lmplot(data=data, x='valence', y='energy', hue='label', 
                   fit_reg=False, legend=True, legend_out=True)
            

#Insert Labels in Base:

data['_id'] = songsdb['_id']
obj_label = data[['_id']]
lab_label = data[['label']]

o = []
l = []
for i in obj_label['_id']:
    o.append(i)
for j in lab_label['label']:
    l.append(j)
d = dict(zip(o, l))  

mongodb.addLabelToSong(d,playlists)

## Decision de k

Sum_of_squared_distances = []
K = range(1,15)
for k in K:
    km = KMeans(n_clusters=k)
    km = km.fit(X_2)
    Sum_of_squared_distances.append(km.inertia_)

for n_clusters in range(2,15):
    clusterer = KMeans (n_clusters=n_clusters)
    preds = clusterer.fit_predict(X_2)
    centers = clusterer.cluster_centers_

    score = silhouette_score (X_2, preds, metric='euclidean')
    print ("For n_clusters = {}, silhouette score is {})".format(n_clusters, score))

plt.plot(K, Sum_of_squared_distances, 'gx-')
plt.xlabel('k')
plt.ylabel('Sum_of_squared_distances')
plt.title('Elbow Method For Optimal k')
plt.show()


## Supervised Learning

db, base = mongodb.connectCollection(database, 'playlists')
data_base = pd.DataFrame(list(base.find({})))
data_base = data_base[data_base['energy'].notnull()]
df_base = data_base[['label','energy','valence','danceability']]
X = df_base.drop(['label'], axis = 1)
y = df_base['label']


steps = [
        StandardScaler(),
         Normalizer(),
]
pipe = make_pipeline(*steps)
X = pipe.fit_transform(X)
data = pd.DataFrame(X)

data.rename(columns={
    0:'energy',
    1:'valence',
    2:'danceability'
}, inplace=True)

X_1 = data[['energy','valence']]


X_train, X_test, y_train, y_test = train_test_split(X_1, y, test_size=0.2)


models = {
    "svm": LinearSVC(),
    "logistic": LogisticRegression(solver='lbfgs', max_iter=2000,multi_class='multinomial'),
    "forest": RandomForestClassifier(),
    'knn': KNeighborsClassifier(),
    'ridge':RidgeClassifier(),
    'nearest_centroid':NearestCentroid(),
    'decision_tree':DecisionTreeClassifier(),
    'bbt':BalancedBaggingClassifier(base_estimator=DecisionTreeClassifier())
    
}

for modelName, model in models.items():
    print(f"Training model: {modelName}")
    model.fit(X_train, y_train)


d = {modelName:model.predict(X_test) for modelName, model in models.items()}
df = pd.DataFrame(d)
df['gt'] = y_test.reset_index(drop=True)
df.head(3)



scores = {}
for modelName, model in models.items():  
    scores[modelName] ={}
for modelName, model in models.items():  
    scores[modelName]['Accuracy'] =round(accuracy_score(df["gt"],df[modelName]),4)
    scores[modelName]['Precision'] =round(precision_score(df["gt"],df[modelName],average='weighted'),4)
    scores[modelName]['Recall'] =round(recall_score(df["gt"],df[modelName],average='weighted'),4)
    scores[modelName]['F1 Score'] =round(f1_score(df["gt"],df[modelName],average='weighted'),4)
pd.DataFrame(scores)

confusion_matrix(df['gt'], df['nearest_centroid'])

nearest_centroid = NearestCentroid()
nearest_centroid.fit(X_1, y)

filename = 'finalized_model.sav'
pickle.dump(nearest_centroid, open(filename, 'wb'))


# load the model from disk
# loaded_model = pickle.load(open(filename, 'rb'))
# result = loaded_model.score(X_test, Y_test)
# print(result)
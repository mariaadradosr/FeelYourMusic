#!/usr/bin/python3

from pymongo import MongoClient
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Normalizer
import pandas as pd
from sklearn.pipeline import make_pipeline
import json
import config
import os
import requests
from bson import ObjectId
import dotenv
import random
from sklearn.neighbors import NearestCentroid

dotenv.load_dotenv()

# CONNECT TO DATABASE  ----------------------------------------------------

connection=os.getenv("ATLAS_URL")
client = MongoClient(connection)

def connectCollection(database, collection):
    print('Conecting to server...')
    db = client[database]
    coll = db[collection]
    print(f'Connected to {connection[:11]}')
    return db, coll

# ADDING DOCUMENT ----------------------------------------------------

def addDocument(document, coll):
    doc = coll.insert_one(document)
    return doc.inserted_id

# CREATING USER ----------------------------------------------------

def createUser(user_info, coll):
    """Adds app user into MongoDB users collection"""
    if len(list(coll.find({'id':user_info['id']}))) == 0:
        return addDocument(user_info, coll)

# INFORMATION REGARDING CURRENT USER SPOTIFY ----------------------------------------------------

def infoMusicUser(sp):
    saved_songs = sp.current_user_saved_tracks()['total']
#     followed_artists = len(sp.current_user_followed_artists()['artists']['items'])
    user_playlists = sp.current_user_playlists()['total']
    playlists_songs = 0
    for playlist in sp.current_user_playlists()['items']:
        playlists_songs += playlist['tracks']['total']
    top_artists = []
    for artist in sp.current_user_top_artists(limit=10)['items']:
        top_artists.append(artist['name'])
    top_artists.append('...')    
    top_tracks = []
    for track in sp.current_user_top_tracks()['items']:
        top_tracks.append(track['name'])
    top_tracks.append('...')  
    return saved_songs, user_playlists, playlists_songs, ', '.join(top_artists), ', '.join(top_tracks)

# FUNCTIONS TO ADD DIFFERENT SOURCES SPOTIFY TRACKS TO MONGODB SONGS COLLECTION AND ALL ITS RELATIVE INFORMATION (USER, FEATURES, CREATED DATE)

def addDifferentSourceTracks(sp, source,coll,current_user,limit=50):
    mongo_songs = [song['spId'] for song in list(coll.find({}))]
    if source =='current_user_saved_tracks':
        total = sp.current_user_saved_tracks(limit=limit, offset=0)['total']
        offsets = [i*limit for i in range(total//limit+1)]
        current_saved_tracks = []
        for offset in offsets:
            results = [song['track']['id'] for song in sp.current_user_saved_tracks(limit=50, offset=offset)['items']]
            current_saved_tracks += results
        songsToAdd = [song for song in current_saved_tracks if song not in mongo_songs]
        addTracksToMongo(sp, songsToAdd,current_user,coll)
        AddInsertTime(coll)
        songsToAddUser = [song for song in current_saved_tracks if song in mongo_songs]
        print(songsToAddUser)
        addUserToTrack(current_user,coll,songsToAddUser)
    elif source =='current_user_top_tracks':
        total = sp.current_user_top_tracks(limit=limit, offset=0)['total']
        offsets = [i*limit for i in range(total//limit+1)]
        current_saved_tracks = []
        for offset in offsets:
            results = [song['id'] for song in sp.current_user_top_tracks(limit=50, offset=offset)['items']]
            current_saved_tracks += results
        songsToAdd = [song for song in current_saved_tracks if song not in mongo_songs]
        addTracksToMongo(sp, songsToAdd,current_user,coll)    
        AddInsertTime(coll)
        songsToAddUser = [song for song in current_saved_tracks if song in mongo_songs]
        print(songsToAddUser)
        addUserToTrack(current_user,coll,songsToAddUser)
    elif source =='current_user_top_artists':
        top_artists = sp.current_user_top_artists(limit=50)['items']
        current_saved_tracks = []
        for artist in top_artists:
            artistId = artist['id']
            results = [song['id'] for song in sp.artist_top_tracks(artistId)['tracks']]
            current_saved_tracks += results
        songsToAdd = [song for song in current_saved_tracks if song not in mongo_songs]
        addTracksToMongo(sp, songsToAdd,current_user,coll)
        AddInsertTime(coll)
        songsToAddUser = [song for song in current_saved_tracks if song in mongo_songs]
        print(songsToAddUser)
        addUserToTrack(current_user,coll,songsToAddUser)

def addTracksToMongo(sp, songsToAdd,current_user,coll):
    for songId in songsToAdd:
                songInfo = sp.track(songId)
                track = songInfo['name']
                document = {
                                'spId' : songInfo['id'],
                                'name' : songInfo['name'],
                                'artistId' : songInfo['artists'][0]['id'],
                                'artist' :  songInfo['artists'][0]['name'],
                                'albumId' : songInfo['album']['id'],
                                'album' :  songInfo['album']['name'],
                                'release_date' :  songInfo['album']['release_date'],
                                'users': [current_user]
                            }
                print(f'{addDocument(document, coll)} [{track}] added to database')

def addUserToTrack(current_user,coll,songsToAddUser):
    for songId in songsToAddUser:
        if current_user not in list(coll.find({'spId':songId}))[0]['users']:
            filtro = {'_id':ObjectId(list(coll.find({'spId':songId}))[0]['_id'])}
            field = 'users'
            value = {'$push':{field:current_user}}
            coll.update_one(filtro, value)
            print(f'{current_user} added to {songId}')

def addFeaturesToSongs(sp, coll):
    for song in list(coll.find({'valence':{'$exists':False}})):
        addFeatures(sp, song['spId'], coll)

def addFeatures(sp, songId, coll):
    try:
        features = sp.audio_features(songId)[0]
        mongoId = list(coll.find({'spId':songId}))[0]['_id']
        filtro = {'_id':ObjectId(mongoId)}
        for item in ['danceability', 'energy', 'key', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']:
            field = item
            value = {'$set':{field:features[field]}}
            coll.update_one(filtro, value)
        print(f'{songId} features added')
    except:
        print('No features for this track')

def getUserPlaylists(user,sp, limit=50):  
    user_playlists = []
    total = sp.user_playlists(user,limit=limit, offset=0)['total']
    offsets = [i*limit for i in range(total//limit+1)]
    for offset in offsets:
        results = sp.user_playlists(user,limit=50, offset=offset)['items']
        for result in results:
            user_playlists.append(result['id'])
    return user_playlists

def addPlaylists(coll, sp, pl_list,user=''):
    mongo_songs = [song['spId'] for song in list(coll.find({}))]
    current_saved_tracks = []
    for playlist_id in pl_list:
        limit = 100
        total = sp.user_playlist_tracks(user='',playlist_id=playlist_id, limit=limit, offset=0)['total']
        offsets = [i*limit for i in range(total//limit+1)]
        for offset in offsets:
            results = [song['track']['id'] for song in sp.user_playlist_tracks(user='',playlist_id=playlist_id,limit=limit, offset=offset)['items']]
            current_saved_tracks += results
    
    songsToAdd = [song for song in list(set(current_saved_tracks)) if song not in mongo_songs]
    addTracksToMongo(sp, songsToAdd,user,coll)
    AddInsertTime(coll)
    songsToAddUser = [song for song in current_saved_tracks if song in mongo_songs]
    addUserToTrack(user,coll,songsToAddUser)

def AddInsertTime(coll):
    documents = list(coll.find({'CreatedTime':{'$exists':False}}))
    if len(documents)>0:
        for item in documents:
            filtro = {'_id':ObjectId(item['_id'])}
            field = 'CreatedTime'
            date = item['_id'].generation_time.date().strftime('%d-%m-%Y')
            value = {'$set':{field:date}}
            coll.update_one(filtro, value)
            print(f'Date added to {filtro}')

# SCALE AND NORMALIZED FEATURES ----------------------------------------------------

def CreateScaleNormDict(base, objetivo):
    try:
        data_base = pd.DataFrame(list(base.find({})))
        data_base = data_base[data_base['energy'].notnull()]
        data_objetivo = pd.DataFrame(list(objetivo.find({'$and':[{'energy':{'$exists':True}},{'energy_sn':{'$exists':False}}]})))
        data_objetivo = data_objetivo[data_objetivo['energy'].notnull()]
        data_objetivo.reset_index(inplace = True, drop = True) 
        n = data_objetivo.shape[0]
        new = pd.concat([data_objetivo,data_base], ignore_index=True, axis=0, join='outer', sort=False)
        X_pre = new[['energy','valence','danceability']]
        steps = [
            StandardScaler(),
            Normalizer(),
            ]
        pipe = make_pipeline(*steps)
        X_pos = pipe.fit_transform(X_pre)
        data_obj = pd.DataFrame(X_pos)
        data_obj.rename(columns={
            0:'energy_sn',
            1: 'valence_sn',
            2:'danceability_sn',}, inplace=True)
        data_obj = data_obj[:n]
        data_obj['_id'] = data_objetivo['_id']
        data_obj = data_obj.drop('danceability_sn', axis=1)
        return data_obj.to_dict(orient='records')
    except:
        return {}

def addScaledNormalizedFeatures(dicc, coll):
    for item in dicc:
        filtro = {'_id':ObjectId(item['_id'])}
        field = 'energy_sn'
        value = {'$set':{field:item['energy_sn']}}
        coll.update_one(filtro, value)
        field = 'valence_sn'
        value = {'$set':{field:item['valence_sn']}}
        coll.update_one(filtro, value)
        print('Standarized and Normalized features added')

# LABELING SONGS ----------------------------------------------------

def CreatelabelsDict(userId,coll,model, base):
    data_objetivo = pd.DataFrame(list(coll.find({'$and':[{'label':{'$exists':False}},{'energy':{'$exists':True}},{'users':{'$eq':userId}}]})))
    if len(data_objetivo)>0:
        data_objetivo = data_objetivo[data_objetivo['energy'].notnull()]
        X = data_objetivo[['energy_sn','valence_sn']]
        y = model.predict(X)
        obj_label = data_objetivo[['_id']]
        o= []
        l = []
        for i in obj_label['_id']:
            o.append(i)
        for j in y:
            l.append(j)
        return   dict(zip(o, l))
    else:
        print('No labels to create')
        return {}

def addLabelToSong(dictionary, coll):
    for key,label in dictionary.items():
        if len(list(coll.find({'$and':[{'_id':ObjectId(key)},{'label':{'$exists':True}}]})))==0:
            filtro = {'_id':ObjectId(key)}
            field = 'label'
            value = {'$set':{field:label}}
            coll.update_one(filtro, value)
            print('song labelled')
        else:
            print('Song already labelled')

# CREATING PLAYLISTS ----------------------------------------------------

def createPlaylist(sp,userId, tracks_id, playlist_name):
    new_playlist = sp.user_playlist_create(userId,playlist_name)
    plId = new_playlist['id']
    random.shuffle(tracks_id)
    sp.user_playlist_add_tracks(userId, plId, tracks_id[:20])
    print(f'{playlist_name} [{plId}] has been created!')
    return plId
    
def getInfoPlaylist(sp, userId, plId):
    user_pl_tracks = sp.user_playlist_tracks(userId,plId)
    songs = [song['track']['name'] for song in user_pl_tracks['items']]
    artists = [song['track']['artists'][0]['name'] for song in user_pl_tracks['items']]
    mix = [i+' ['+j+']' for i,j in zip(songs, artists)]
    return ', '.join(mix)





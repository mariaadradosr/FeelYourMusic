from flask import Flask, redirect, request, session,g, render_template, url_for
import spotipy
import spotify
import config
import os
from urllib.parse import quote
import requests
import json
import functions
import pickle
import re
import spreadsheet

app = Flask(__name__)

plId = None
userId = None
sp = None

database = 'spotify'
db, songs = functions.connectCollection(database,'songs_prueba')
db, users = functions.connectCollection(database,'users')
db, playlists = functions.connectCollection(database,'playlists')

#  Client Keys
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

CLIENT_SIDE_URL = "http://localhost"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/".format(CLIENT_SIDE_URL, PORT)
SCOPE = os.getenv("SCOPE")
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

@app.route("/auth")
def auth():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    print(auth_url)
    return redirect(auth_url)

@app.route("/callback/")
def callback():
    global userId
    global sp
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)
    
    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    # refresh_token = response_data["refresh_token"]
    # token_type = response_data["token_type"]
    # expires_in = response_data["expires_in"]

    # with open('auth.json', 'w') as outfile:
    #     json.dump(response_data, outfile)
    # with open('auth.json') as json_file:
    #     data = json.load(json_file)
    sp= spotipy.Spotify(auth=access_token)
    userId = sp.current_user()['id']
    # Auth Step 6: Use the access token to access Spotify API
    # authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
def index():
    global sp
    global userId
    # with open('auth.json') as json_file:
    #     data = json.load(json_file)
    # print(data)
    # sp= spotipy.Spotify(auth=data['access_token'])
    name = sp.current_user()['display_name']
    # userId = sp.current_user()['id']
    if len(list(users.find({'id':userId}))) == 0:
        functions.createUser(sp.current_user(), users)
        saved_songs, user_playlists,playlists_songs, top_artists, top_tracks = functions.infoMusicUser(sp)
        return render_template("index.html", name = name, saved_songs=saved_songs,
                                playlists_songs = playlists_songs,
                                user_playlists=user_playlists,top_artists=top_artists,
                                top_tracks=top_tracks)
    else:
        total = len(list(songs.find({'users':{'$in': [userId] }})))
        saved_songs, user_playlists,playlists_songs, top_artists, top_tracks = functions.infoMusicUser(sp)
        return render_template('index_re.html', name=name, total = total,
                                saved_songs=saved_songs,
                                playlists_songs = playlists_songs,
                                user_playlists=user_playlists,top_artists=top_artists,
                                top_tracks=top_tracks)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/upload', methods=["GET", "POST"])
def upload():
    global sp
    global userId
    if request.method == 'POST':
        upload_preferences = request.form.getlist('mycheckbox')
        print(upload_preferences)
        if len(upload_preferences) ==0:
            feedback = f"You have to check at least one option"
            return render_template('upload.html', feedback=feedback)
        else:
            # with open('auth.json') as json_file:
            #     data = json.load(json_file)
            # sp= spotipy.Spotify(auth=data['access_token'])
            # userId = sp.current_user()['id']
            for preference in upload_preferences:
                if preference in ['current_user_top_tracks','current_user_saved_tracks','current_user_top_artists']:
                    functions.addDifferentSourceTracks(sp,preference,songs,userId)
                    print('Songs add ended ---------------------------------------------')
                    functions.addFeaturesToSongs(sp,songs)
                    print('Features add ended ---------------------------------------------')
                    dicc = functions.CreateScaleNormDict(playlists, songs)
                    print('Scaled and Normalized Features dicctionary created ----------------------',len(dicc))
                    print(dicc)
                    if len(dicc) >0:
                        functions.addScaledNormalizedFeatures(dicc, songs)
                        print('Scaled and Normalized Features add end ---------------------------------------------')
                elif preference == 'current_user_playlists':
                    pl_list = functions.getUserPlaylists(userId,sp)
                    functions.addPlaylists(songs,sp,pl_list,user=userId)
                    print('Songs add ended ---------------------------------------------')
                    functions.addFeaturesToSongs(sp,songs)
                    print('Features add ended ---------------------------------------------')
                    dicc = functions.CreateScaleNormDict(playlists, songs)
                    print('Scaled and Normalized Features dicctionary created ----------------------',len(dicc))
                    if len(dicc) >0:
                        functions.addScaledNormalizedFeatures(dicc, songs)
                        print('Scaled and Normalized Features add end ---------------------------------------------')
            loaded_model = pickle.load(open('./finalized_model.sav', 'rb'))
            print(loaded_model)
            dictionary= functions.CreatelabelsDict(userId,songs,loaded_model,playlists)
            print('label dictionay created --------------', len(dictionary))
            if len(dictionary)>0:
                functions.addLabelToSong(dictionary, songs)
            print('<<<<<<<<<<<<<<UPLOAD ENDED>>>>>>>>>>>>>>')
        return redirect(url_for('feeling'))
    return render_template('upload.html')

@app.route('/feeling', methods=["GET", "POST"])
def feeling():
    global plId
    global sp
    global userId
    if request.method == 'POST':
        print(userId)
        # with open('auth.json') as json_file:
        #     data = json.load(json_file)
        # sp= spotipy.Spotify(auth=data['access_token'])
        # userId = sp.current_user()['id']
        number = request.form.get('number')
        danceability = request.form.getlist('danceability')
        playlist_name = request.form.get('plname')
        print(number, danceability, playlist_name)
        if number not in ['0','1','2','3','4','5'] or (len(re.findall(r'^(?:[0-9]|0[1-9]|10)$',danceability[0]))==0 or len(re.findall(r'^(?:[0-9]|0[1-9]|10)$',danceability[1]))==0):
            feedback = f"Cluster [0 , 5] / Min-Max [0, 10]"
            return render_template('feeling.html', feedback=feedback)
        else:
            if danceability[0] =='':
                min_dance = 0/100
            if danceability[1] =='':
                max_dance = 1/100
            else:
                min_dance = int(danceability[0])/10
                max_dance = int(danceability[1])/10
            pipeline =[
                        {
                            '$match': {
                                'users': userId, 
                                'label': int(number), 
                                'danceability': {
                                    '$gte': min_dance, 
                                    '$lte': max_dance
                                }
                            }
                        }, {
                            '$project': {
                                'spId': 1
                            }
                        }
                    ]
            print(pipeline)
            user_election = list(songs.aggregate(pipeline))
            tracks_id = [item['spId']for item in user_election]
            print(number, min_dance, max_dance, userId, playlist_name)
            print(tracks_id)
            plId =functions.createPlaylist(sp,userId, tracks_id, playlist_name)
            tableau_pipeline = [
                    {
                        '$match': {
                            'users': 'meyerson'
                        }
                    }, {
                        '$project': {
                            '_id':0,
                            'spId':1,
                            'name': 1, 
                            'artist': 1, 
                            'album': 1, 
                            'label': 1, 
                            'release_date': 1, 
                            'energy_sn': 1, 
                            'valence_sn': 1, 
                            'danceability': 1
                        }
                    }
                ]
            user_tableau = list(songs.aggregate(tableau_pipeline))
            with open(f'./output/{userId}.json', 'w') as outfile:
                json.dump(user_tableau, outfile)
            spreadsheet.saveUserInfo(userId)
            return redirect(url_for('results'))
    return render_template("feeling.html")

@app.route('/results')
def results():
    global plId
    global userId
    global sp
    print(plId)
    tracksCreated = functions.getInfoPlaylist(sp, userId, plId)
    return render_template('results.html', tracksCreated=tracksCreated)


@app.route('/thanku')
def thanku():
    global plId
    global userId
    global sp
    print(plId)
    name = sp.current_user()['display_name']
    return render_template('thanku.html', name=name )

if __name__ == "__main__":
    app.run(debug=True)


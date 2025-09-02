import os
import spotipy
import json
import requests
from spotipy.oauth2 import SpotifyOAuth

# funtion authenticate reads spotify_crendetials.json to authenticate access to the api
# return object Spotify
def authenticate():
    json_file = open("spotify_credentials.json", "r")
    creds = json.loads(json_file.read())
    spotipy_client_id = creds["spotipy_client_id"]
    spotipy_client_secret = creds["spotipy_client_secret"]
    spotipy_redirect_uri = creds["redirect_uri"]

    auth_manager = SpotifyOAuth(client_id=spotipy_client_id, client_secret=spotipy_client_secret, redirect_uri=spotipy_redirect_uri, scope="user-top-read",
    cache_path=".spotipy_cache")
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

#function to get the response from current user top tracks
#return list of dict of top 5 songs, including title, artist name, local path for album cover
#dict include "name", "artist", "image"
def get_data():
    sp = authenticate()
    resp = sp.current_user_top_tracks(limit=5, time_range="short_term")
    result = []
    i = 1 # i is for generating file name
    for tr in resp["items"]:
        track = {}
        track["name"] = tr["name"]
        track["artist"] = tr["artists"][0]["name"]
        img_url= tr["album"]["images"][0]["url"]
        filename = f"images/image-{i:02d}.jpg"
        track["image"] = filename
        i+=1

        #download the image
        r = requests.get(img_url, stream=True)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print("Saved:", filename)
        else:
            print("Failed to download:", img_url)
        
        result.append(track)

    return result



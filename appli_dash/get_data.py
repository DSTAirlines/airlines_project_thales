#!/usr/bin/python3
import os
import sys
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")
sys.path.append(f"{parent_dir}/live_api")

# Importer la fonction de connexion à MongoDB
from connection_mongodb import get_connection

# Importer la fonction d'appel à l'API OpenSky
from fetch_opensky_data import query_opensky_api

# CREDENTIALS
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
CLIENT_ID_LUFTHANSA = os.environ.get("CLIENT_ID_LUFTHANSA")
CLIENT_SECRET_LUFTHANSA = os.environ.get("CLIENT_SECRET_LUFTHANSA")


def get_data_initial():
    # A l'ouverture de la page de la map Dash
    # Permet de récupérer les données qui matchent entre data Airlabs et dernier enregistrement OpenSky

    client = get_connection()
    db = client[MONGO_DB_NAME]
    opensky_collection = db[MONGO_COL_OPENSKY]

    # Recherche du "time" le plus récent
    max_time_result = opensky_collection.find().sort("time", -1).limit(1)
    max_time = max_time_result[0]["time"]

    # Recherche des documents du dernier enregistrement avec un airlabs_id non nul
    pipeline = [
        {"$match": {"time": max_time, "airlabs_id": {"$ne": None}}},
        {"$lookup": {
            "from": "airlabs",
            "localField": "airlabs_id",
            "foreignField": "_id",
            "as": "airlabs_doc"
        }},
        {"$unwind": "$airlabs_doc"},
    ]

    results = list(opensky_collection.aggregate(pipeline))
    return results


def get_data_dynamic_updated(old_data):
    
    # Quand refresh de la page map Dash, appel à l'API OpenSky
    # on ne va garder que les old_data dont le callsign est présent dans le nouvel appel API
    opensky_data = query_opensky_api()
    old_callsigns = [list(d.keys())[0] for d in old_data]
    return [data for data in opensky_data if data['callsign'] in old_callsigns]



# def get_info_flight_number(callsign):

#     now = datetime.now()
#     refresh_time = now.strftime("%Y-%m-%d")

#     auth_url = "https://api.lufthansa.com/v1/oauth/token"
#     auth_payload = {
#         "client_id": CLIENT_ID_LUFTHANSA,
#         "client_secret": CLIENT_SECRET_LUFTHANSA,
#         "grant_type": "client_credentials"
#     }
#     auth_response = requests.post(auth_url, data=auth_payload)
#     auth_data = auth_response.json()

#     token = auth_data["access_token"]
#     headers = {"Authorization": f"Bearer {token}"}
#     params = {"limit": limit, "offset": offset}

#     url = BASE_URL_REFERENCES + endpoint
#     r = requests.get(url, headers=headers, params=params)

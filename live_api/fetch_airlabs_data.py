#!/usr/bin/python3
import os
import requests
import time
from pymongo import MongoClient
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection

# CREDENTIALS
KEY_AIRLABS_API = os.environ.get("KEY_AIRLABS_API")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")

def query_airlabs_api():

    time_now = int(time.time())
    params = {
        'api_key' : KEY_AIRLABS_API,
        'bbox': (pr.la_min, pr.lon_min, pr.la_max, pr.lon_max)
    }
    url = pr.ROOT_AIRLABS_URL

    response = requests.get(url, params)
    result = response.json()
    airlabs_data = result['response']

    for state in airlabs_data:
        state['time'] = time_now
        state['datatime'] = datetime.utcfromtimestamp(time_now).strftime('%Y-%m-%d %H:%M:%S')
        if 'flight_icao' not in state.keys(): 
            state['flight_icao'] = None

    return airlabs_data

def lauch_script():
    airlabs_data = query_airlabs_api()
    client = get_connection()
    db = client[MONGO_DB_NAME]
    collection_opensky = db[MONGO_COL_OPENSKY]
    collection_airlabs = db[MONGO_COL_AIRLABS]

    # Insérer les documents airlabs_data dans la collection airlabs
    collection_airlabs.insert_many(airlabs_data)

    # Trouver les documents opensky qui ont un "airlabs_id" nul ou vide
    opensky_no_airlabs_id = collection_opensky.find({"airlabs_id": {"$in": [None, ""]}})

    # Vérifier la correspondance entre les documents opensky et airlabs_data, puis mettre à jour les documents opensky
    for opensky_doc in opensky_no_airlabs_id:
        callsign = opensky_doc["callsign"]
        airlabs_match = next((doc for doc in airlabs_data if doc["flight_icao"] == callsign), None)
        if airlabs_match:
            # Mettre à jour les documents opensky avec l'airlabs_id correspondant
            collection_opensky.update_one({"_id": opensky_doc["_id"]}, {"$set": {"airlabs_id": airlabs_match["_id"]}})

    # Supprimer les documents opensky sans correspondance (airlabs_id nul ou vide)
    collection_opensky.delete_many({"airlabs_id": {"$in": [None, ""]}})

    # on ferme la connexion
    client.close()

lauch_script()


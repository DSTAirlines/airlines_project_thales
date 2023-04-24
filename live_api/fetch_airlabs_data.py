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
        state['fly_id'] = None
        state['time'] = time_now
        state['datatime'] = datetime.utcfromtimestamp(time_now).strftime('%Y-%m-%d %H:%M:%S')
        if 'flight_icao' in state.keys() and 'hex' in state.keys():
            if state['flight_icao'] is not None and state['hex'] is not None:
                state['fly_id'] = f"{state['flight_icao']}-{state['hex']}"

    return airlabs_data

def lauch_script():
    airlabs_data = query_airlabs_api()
    client = get_connection()
    db = client[MONGO_DB_NAME]
    collection_opensky = db[MONGO_COL_OPENSKY]
    collection_airlabs = db[MONGO_COL_AIRLABS]

    # Insérer les documents airlabs_data dans la collection airlabs
    collection_airlabs.insert_many(airlabs_data)

    # Trouver les correspondances entre les collections opensky et airlabs et mettre à jour les documents opensky
    for airlabs_doc in airlabs_data:
        fly_id = airlabs_doc["fly_id"]
        match = collection_opensky.find_one({"fly_id": fly_id, "airlabs_id": None})
        if match:
            # Mettre à jour les documents opensky avec l'airlabs_id correspondant
            collection_opensky.update_many({"fly_id": fly_id}, {"$set": {"airlabs_id": airlabs_doc["_id"]}})

    # Supprimer les documents opensky sans correspondance (airlabs_id nul ou vide)
    collection_opensky.delete_many({"airlabs_id": {"$in": [None, ""]}})

    # on ferme la connexion
    client.close()

lauch_script()


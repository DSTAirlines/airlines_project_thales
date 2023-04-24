#!/usr/bin/python3
import os
from opensky_api import OpenSkyApi
import properties as pr
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
USER_OPENSKY_API = os.environ.get("USER_OPENSKY_API")
PASS_OPENSKY_API = os.environ.get("PASS_OPENSKY_API")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")


def query_opensky_api():
    opensky_data = []
    open_sky_api = OpenSkyApi(username=USER_OPENSKY_API, password=PASS_OPENSKY_API)

    response = open_sky_api.get_states(bbox=(pr.la_min, pr.la_max, pr.lon_min, pr.lon_max))
    time_unix = response.time
    states = response.states

    opensky_data = [{
        "time": time_unix,
        "datatime": datetime.utcfromtimestamp(time_unix).strftime('%Y-%m-%d %H:%M:%S') if time_unix else None,
        "airlabs_id": None,
        "icao_24": state.icao24.strip().upper() if state.icao24 else None,
        "callsign": state.callsign.strip().upper() if state.callsign else None,
        "origin_country": state.origin_country.strip() if state.origin_country else None,
        "time_position": state.time_position,
        "last_contact": state.last_contact,
        "longitude": state.longitude,
        "latitude": state.latitude,
        "baro_altitude": state.baro_altitude,
        "geo_altitude": state.geo_altitude,
        "velocity": state.velocity,
        "cap": state.true_track,
        "vertical_rate": state.vertical_rate,
        "on_ground": state.on_ground,
    } for state in states]

    return opensky_data


def lauch_script():
    opensky_data = query_opensky_api()
    client = get_connection()
    db = client[MONGO_DB_NAME]
    collection_opensky = db[MONGO_COL_OPENSKY]
    collection_airlabs = db[MONGO_COL_AIRLABS]
    nb_docs_airlabs = collection_airlabs.count_documents({})

    if nb_docs_airlabs > 0:
        # Vérifier si le fly_id est déjà présent dans la collection opensky
        for opensky_doc in opensky_data:
            callsign = opensky_doc["callsign"]
            match = collection_opensky.find_one({"callsign": callsign})
            # si oui, on récupère la valeur de airlabs_id
            if match and "airlabs_id" in match:
                opensky_doc["airlabs_id"] = match["airlabs_id"]

    collection_opensky.insert_many(opensky_data)

    # On ferme la connexion
    client.close()

lauch_script()

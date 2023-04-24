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
sys.path.append(f"{parent_dir}/fetch_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection

# CREDENTIALS
USER_OPENSKY_API = os.environ.get("USER_OPENSKY_API")
PASS_OPENSKY_API = os.environ.get("PASS_OPENSKY_API")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")

def query_opensky_api():

    list_state = []
    open_sky_api = OpenSkyApi(username=USER_OPENSKY_API, password=PASS_OPENSKY_API)

    response = open_sky_api.get_states(bbox=(pr.la_min, pr.la_max, pr.lon_min, pr.lon_max))
    time = response.time
    states = response.states

    for state in states:
        list_state.append({
            "time" : time,
            "icao_24" : state.icao24,
            "call_sign" : state.callsign,
            "origin_country" : state.origin_country,
            "time_position" : state.time_position,
            "last_contact" : state.last_contact,
            "longitude" : state.longitude,
            "latitude" : state.latitude,
            "baro_altitude" : state.baro_altitude,
            "geo_altitude" : state.geo_altitude,
            "velocity" : state.velocity,
            "cap" : state.true_track,
            "vertical_rate": state.vertical_rate,
            "on_ground" : state.on_ground,
        })
    
    return list_state

def lauch_script():
    list_state = query_opensky_api()
    client = get_connection()
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COL_OPENSKY]

    collection.insert_many(list_state)

lauch_script()

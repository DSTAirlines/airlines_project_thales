#!/usr/bin/python3
import os
import requests
import time
from datetime import datetime
import properties as pr
import sys
from pathlib import Path
from utilities_live_api import convert_time_unix_utc_to_datetime_fr
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection

# CREDENTIALS
KEY_AIRLABS_API = os.environ.get("KEY_AIRLABS_API")
KEY_AIRLABS_API_CRONJOB = os.environ.get("KEY_AIRLABS_API_CRONJOB")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")

def query_airlabs_api(cron=False):
    """
    AppelAPI Airlabs
    Args:
        cron (bool, optional): Utilisation d'un compte API différent pour 
            le cronjob (True par défaut).
    Returns:
        Array: Array de dict des résultats de l'appel API
    """

    time_now = int(time.time())
    params = {
        'api_key' : KEY_AIRLABS_API_CRONJOB if cron is True else KEY_AIRLABS_API,
        'bbox': (pr.la_min, pr.lon_min, pr.la_max, pr.lon_max)
    }
    url = pr.ROOT_AIRLABS_URL

    response = requests.get(url, params)

    if response.status_code != 200:
        raise Exception(f"Status: error\n{response.status_code} {response.reason}")

    result = response.json()
    states = result['response']

    airlabs_data = [{
        "time": time_now,
        "datatime": convert_time_unix_utc_to_datetime_fr(time_now) if time_now else None,
        "hex": state.get('hex', None),
        "reg_number": state.get('reg_number', None),
        "flag": state.get('flag', None),
        "flight_number": state.get('flight_number', None),
        "flight_icao": state.get('flight_icao', None),
        "flight_iata": state.get('flight_iata', None),
        "dep_icao": state.get('dep_icao', None),
        "dep_iata": state.get('dep_iata', None),
        "arr_icao": state.get('arr_icao', None),
        "arr_iata": state.get('arr_iata', None),
        "airline_icao": state.get('airline_icao', None),
        "airline_iata": state.get('airline_iata', None),
        "aircraft_icao": state.get('aircraft_icao', None),
        "status": state.get('status', None),
    } for state in states]

    return airlabs_data



def lauch_script(init=False, cron=False):
    """
    Script de traitement et d'enregistrement des résultats de l'API
        Principe: Vérifier dans collection Opensky si correspondance avec callsign
            - si oui: mise à jour document OpenSky avec identifiant Airlabs et
              enregistrement du document Airlabs
            - si non: suppression du document de la collection OpenSky
    Args:
        cron (bool, optional): Utilisation d'un compte API différent pour 
            le cronjob (True par défaut).
    """
    
    # Récupération data API
    airlabs_data = query_airlabs_api(cron=cron)

    # Connexion MongoDB
    client = get_connection()
    db = client[MONGO_DB_NAME]
    collection_opensky = db[MONGO_COL_OPENSKY]
    collection_airlabs = db[MONGO_COL_AIRLABS]

    if init:
        collection_airlabs.insert_many(airlabs_data)

    else:
        # Récupération du time du dernier appel API Airlabs 
        max_time_airlabs_result = collection_airlabs.find().sort("time", -1).limit(1)
        max_time_airlabs = max_time_airlabs_result[0]["time"]

        # Création d'un dictionnaire basé sur 'flight_icao' pour accélérer la recherche de correspondances
        airlabs_dict = {airlab["flight_icao"]: airlab for airlab in airlabs_data}

        # Filtrer les documents opensky avec des 'callsign' correspondant aux 'flight_icao' de 'airlabs_data'
        opensky_matching_callsigns = collection_opensky.find({
            "airlabs_id": None,
            "time": {"$gt": max_time_airlabs},
            "callsign": {"$in": list(airlabs_dict.keys())}
        }).sort("callsign")

        # Parmi les documents qui matchent :
        list_opensky = list(opensky_matching_callsigns)
        callsigns = list(set([dic['callsign'] for dic in list_opensky]))

        for callsign in callsigns:
            match = airlabs_dict[callsign]
            match_copy = match.copy()
            airlabs_id = collection_airlabs.insert_one(match_copy).inserted_id

            # Mettre à jour les document opensky avec le champ airlabs_id
            collection_opensky.update_many(
                {"callsign": callsign, "time": {"$gt": max_time_airlabs}},
                {"$set": {"airlabs_id": airlabs_id}}
            )

        # Supprimer les documents opensky sans airlabs_id
        collection_opensky.delete_many({"airlabs_id": {"$in": [None, ""]}})

    # on ferme la connexion
    client.close()

#!/usr/bin/python3
import os
import requests
import time
from datetime import datetime
from requests.exceptions import ConnectionError
import pytz
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection as connect_mongodb

# CREDENTIALS
KEY_AIRLABS_API = os.environ.get("KEY_AIRLABS_API")
MONGO_DATABASE = os.environ.get("MONGO_INITDB_DATABASE")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
ROOT_AIRLABS_URL = os.environ.get("ROOT_AIRLABS_URL")

# SURFACE WITH LONGITUDE & LATITUDE (SQUARE)
la_min = 35.93302587741835
la_max = 71.40896420697621
lon_min = -11.360649771804841
lon_max = 32.017698096436696


# Convertir un timestamp Unix en datetime FR
def convert_time_unix_utc_to_datetime_fr(time_unix_utc):
    # Convertir le timestamp Unix en objet datetime UTC
    utc_datetime = datetime.utcfromtimestamp(time_unix_utc)

    # Définir le fuseau horaire français
    paris_tz = pytz.timezone("Europe/Paris")

    # Convertir l'objet datetime UTC en objet datetime avec le fuseau horaire français
    local_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(paris_tz)

    # Formater l'objet datetime en chaîne de caractères
    datetime_fr = local_datetime.strftime('%Y-%m-%d %H:%M:%S')

    return datetime_fr


def query_airlabs_api():
    """
    AppelAPI Airlabs
    Returns:
        Array: Array de dict des résultats de l'appel API
    """

    time_now = int(time.time())
    params = {
        'api_key' : KEY_AIRLABS_API,
        'bbox': (la_min, lon_min, la_max, lon_max)
    }

    max_retries = 5
    retry_delay = 5  # seconds

    for _ in range(max_retries):
        try:
            response = response = requests.get(ROOT_AIRLABS_URL, params)
            break
        except ConnectionError:
            print('ConnectionError: Failed to resolve airlabs.co Retrying in {} seconds...'.format(retry_delay))
            time.sleep(retry_delay)
    else:
        raise Exception('Failed to resolve oairlabs.co after {} retries'.format(max_retries))

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


def lauch_script():
    """
    Script de traitement et d'enregistrement des résultats de l'API
    Principe: Vérifier dans collection Opensky si correspondance avec callsign
        - si oui: mise à jour document OpenSky avec identifiant Airlabs et
            enregistrement du document Airlabs
        - si non: suppression du document de la collection OpenSky
    """

    # Récupération data API
    airlabs_data = query_airlabs_api()

    # Connexion MongoDB
    client = connect_mongodb()
    db = client[MONGO_DATABASE]
    collection_opensky = db[MONGO_COL_OPENSKY]
    collection_airlabs = db[MONGO_COL_AIRLABS]

    # Création d'un dictionnaire basé sur 'flight_icao' pour accélérer la recherche de correspondances
    airlabs_dict = {airlab["flight_icao"]: airlab for airlab in airlabs_data}

    init = False if collection_airlabs.find_one() is not None else True
    if not init:
        # Récupération du time du dernier appel API Airlabs 
        max_time_airlabs_result = collection_airlabs.find().sort("time", -1).limit(1)
        max_time_airlabs = max_time_airlabs_result[0]["time"]

        # Filtrer les documents opensky avec des 'callsign' correspondant aux 'flight_icao' de 'airlabs_data'
        opensky_matching_callsigns = collection_opensky.find({
            "airlabs_id": None,
            "time": {"$gt": max_time_airlabs},
            "callsign": {"$in": list(airlabs_dict.keys())}
        }).sort("callsign")
    
    else:
        # Filtrer les documents opensky avec des 'callsign' correspondant aux 'flight_icao' de 'airlabs_data'
        opensky_matching_callsigns = collection_opensky.find({
            "airlabs_id": None,
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
        if not init:
            collection_opensky.update_many(
                {"callsign": callsign, "time": {"$gt": max_time_airlabs}},
                {"$set": {"airlabs_id": airlabs_id}}
            )

        else:
            collection_opensky.update_many(
                {"callsign": callsign},
                {"$set": {"airlabs_id": airlabs_id}}
            )

    # Supprimer les documents opensky sans airlabs_id
    collection_opensky.delete_many({"airlabs_id": {"$in": [None, ""]}})

    # on ferme la connexion
    client.close()


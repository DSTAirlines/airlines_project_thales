#!/usr/bin/python3
import os
import properties as pr
import sys
import time
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
from utilities_live_api import convert_time_unix_utc_to_datetime_fr
from pprint import pprint
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
USER_OPENSKY_API_CRONJOB = os.environ.get("USER_OPENSKY_API_CRONJOB")
PASS_OPENSKY_API_CRONJOB = os.environ.get("PASS_OPENSKY_API_CRONJOB")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")


def query_opensky_api(cron=False):
    """
    Appel API OpenSky
    Args:
        cron (bool, optional): Utilisation d'un compte API différent pour 
            le cronjob (True par défaut).
    Returns:
        Array: Array de dict des résultats de l'appel API
    """
    
    # Récupérer les variables d'environnement
    USER = USER_OPENSKY_API_CRONJOB if cron else USER_OPENSKY_API
    PASS = PASS_OPENSKY_API_CRONJOB if cron else PASS_OPENSKY_API
    BASE_URL = pr.ROOT_OPENSKY_URL

    # Initialisation des data
    opensky_data = []
    states=[]

    # Définition des headers
    headers = {
        "Accept": "application/json"
    }

    # Authorization Basic
    basicAuth = HTTPBasicAuth(USER, PASS)
    # Définition de l'url de la requête
    url = f"{BASE_URL}/states/all?lamin={pr.la_min}&lomin={pr.lon_min}&lamax={pr.la_max}&lomax={pr.lon_max}"

    # Requête API OpenSky
    response = requests.get(url, auth=basicAuth, headers=headers)

    if response.status_code == 200:

        # Insérer du time et du datetime format FR
        time_now = int(time.time())
        datetime_fr = convert_time_unix_utc_to_datetime_fr(time_now)

        # Traitement des données renvoyées par l'API
        response_data = response.json()
        if 'states' in response_data:
            states = response_data["states"]
            opensky_data = [{
                "time": time_now,
                "datatime": datetime_fr if time_now else None,
                "airlabs_id": None,
                "icao_24": state[0].strip().upper() if state[0] else None,
                "callsign": state[1].strip().upper() if state[1] else None,
                "origin_country": state[2].strip() if state[2] else None,
                "time_position": state[3],
                "last_contact": state[4],
                "longitude": state[5],
                "latitude": state[6],
                "baro_altitude": state[7],
                "geo_altitude": state[13],
                "velocity": state[9],
                "cap": state[10] if state[10] is not None else 0,
                "vertical_rate": state[11],
                "on_ground": state[8],
            } for state in states if state[1] and state[5] and state[6]]
            return opensky_data

        else:
            raise Exception("Status: error\nDonnées renvoyées par l'API incorrectes")
    else:
        raise Exception(f"Status: error\n{response.status_code} {response.reason}")


def lauch_script(init=False, cron=False):
    """
    Script de traitement et d'enregistrement des résultats de l'API
        Principe: Vérifier dans l'enregistrement précédent la présence d'une 
            correspondance avec Airlab (Airlab_id):
                - si oui: on ajoute cette valeur au nouveau document
    Args:
        init (bool, otionnal): Ne pas appliquer les traitements lors du premier
            appel à l'API lors de la création de la base (False par défaut)
        cron (bool, optional): Utilisation d'un compte API différent pour 
            le cronjob (True par défaut).
    """

    # Récupération data API
    opensky_data = query_opensky_api(cron=cron)

    # Connexion MongoDB
    client = get_connection()
    db = client[MONGO_DB_NAME]
    collection_opensky = db[MONGO_COL_OPENSKY]

    # Ne pas appliquer lors de la création de la base de données
    if init is False:

        # Recherche du "time" le plus récent
        max_time_result = collection_opensky.find().sort("time", -1).limit(1)
        max_time = max_time_result[0]["time"]

        # Vérifier si le callsign est déjà présent dans l'enregistrement précédent
        for opensky_doc in opensky_data:
            callsign = opensky_doc["callsign"]
            match = collection_opensky.find_one({"time": max_time, "callsign": callsign})

            # si oui, on récupère la valeur de airlabs_id
            if match and match["airlabs_id"]:
                opensky_doc["airlabs_id"] = match["airlabs_id"]

    # On insère les documents dans la collection OpenSky
    collection_opensky.insert_many(opensky_data)

    # On ferme la connexion
    client.close()

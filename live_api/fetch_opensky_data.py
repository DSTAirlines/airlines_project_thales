#!/usr/bin/python3
import os
from opensky_api import OpenSkyApi
import properties as pr
import sys
import time
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

    USER = USER_OPENSKY_API_CRONJOB if cron else USER_OPENSKY_API
    PASS = PASS_OPENSKY_API_CRONJOB if cron else PASS_OPENSKY_API
    opensky_data = []
    open_sky_api = OpenSkyApi(username=USER, password=PASS)
    response = open_sky_api.get_states(bbox=(pr.la_min, pr.la_max, pr.lon_min, pr.lon_max))
    states = response.states

    time_now = int(time.time())
    datetime_fr = convert_time_unix_utc_to_datetime_fr(time_now)

    opensky_data = [{
        "time": time_now,
        "datatime": datetime_fr if time_now else None,
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
    } for state in states if state.callsign and state.longitude \
        and state.latitude and state.true_track is not None]

    return opensky_data


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
            if match and "airlabs_id" in match:
                opensky_doc["airlabs_id"] = match["airlabs_id"]

    # On insère les documents dans la collection OpenSky
    collection_opensky.insert_many(opensky_data)

    # On ferme la connexion
    client.close()

# lauch_script()

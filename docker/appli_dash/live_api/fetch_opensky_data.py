#!/usr/bin/python3
import os
import sys
import time
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from datetime import datetime
import pytz
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection as connect_mongodb

# CREDENTIALS
USER_OPENSKY_API = os.environ.get("USER_OPENSKY_API")
PASS_OPENSKY_API = os.environ.get("PASS_OPENSKY_API")
MONGO_DATABASE = os.environ.get("MONGO_INITDB_DATABASE")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
ROOT_OPENSKY_URL = os.environ.get("ROOT_OPENSKY_URL")

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


def query_opensky_api():
    """
    Appel API OpenSky
    Returns:
        Array: Array de dict des résultats de l'appel API
    """

    # Initialisation des data
    opensky_data = []
    states=[]

    # Définition des headers
    headers = {
        "Accept": "application/json"
    }

    # Authorization Basic
    basicAuth = HTTPBasicAuth(USER_OPENSKY_API, PASS_OPENSKY_API)
    # Définition de l'url de la requête
    url = f"{ROOT_OPENSKY_URL}/states/all?lamin={la_min}&lomin={lon_min}&lamax={la_max}&lomax={lon_max}"

    max_retries = 5
    retry_delay = 5  # seconds

    for _ in range(max_retries):
        try:
            # Requête API OpenSky
            response = requests.get(url, auth=basicAuth, headers=headers)
            break
        except ConnectionError:
            print('ConnectionError: Failed to resolve opensky-network.org. Retrying in {} seconds...'.format(retry_delay))
            time.sleep(retry_delay)
    else:
        raise Exception('Failed to resolve opensky-network.org after {} retries'.format(max_retries))

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


def lauch_script():
    """
    Script de traitement et d'enregistrement des résultats de l'API
    Principe: Vérifier dans l'enregistrement précédent la présence d'une 
    correspondance avec Airlab (Airlab_id):
        - si oui: on ajoute cette valeur au nouveau document
    """

    # Récupération data API
    opensky_data = query_opensky_api()

    # Connexion MongoDB
    client = connect_mongodb()
    db = client[MONGO_DATABASE]
    collection_opensky = db[MONGO_COL_OPENSKY]

    # Test présence de document dans la collection OpenSky
    test_opensky = collection_opensky.find_one()
    if test_opensky is not None:
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

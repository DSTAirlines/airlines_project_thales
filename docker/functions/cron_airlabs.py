import os
import requests
import time
from requests.exceptions import ConnectionError
from connection_mongodb import get_connection as connect_mongodb
from utilities_live_api import convert_time_unix_utc_to_datetime_fr
from dotenv import load_dotenv
load_dotenv()


# CREDENTIALS
KEY_AIRLABS_API = os.environ.get("KEY_AIRLABS_API_CRONJOB")
MONGO_DATABASE = os.environ.get("MONGO_INITDB_DATABASE")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
ROOT_AIRLABS_URL = os.environ.get("ROOT_AIRLABS_URL")

# SURFACE WITH LONGITUDE & LATITUDE (SQUARE)
la_min = 35.93302587741835
la_max = 71.40896420697621
lon_min = -11.360649771804841
lon_max = 32.017698096436696


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
        raise Exception('Failed to resolve airlabs.co after {} retries'.format(max_retries))

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
    print(f"Airlabs data : {len(airlabs_data)}")

    # Connexion MongoDB
    client = connect_mongodb()
    db = client[MONGO_DATABASE]
    collection_opensky = db[MONGO_COL_OPENSKY]
    collection_airlabs = db[MONGO_COL_AIRLABS]

    # Création d'un dictionnaire basé sur 'flight_icao' pour accélérer la recherche de correspondances
    airlabs_dict = {airlab["flight_icao"]: airlab for airlab in airlabs_data}

    # Récupération du time du dernier appel API Airlabs 
    max_time_airlabs_result = collection_airlabs.find().sort("time", -1).limit(1)
    max_time_airlabs = max_time_airlabs_result[0]["time"]
    print(f"Max time Airlabs : {max_time_airlabs}")

    # Filtrer les documents opensky avec des 'callsign' correspondant aux 'flight_icao' de 'airlabs_data'
    opensky_matching_callsigns = collection_opensky.find({
        "airlabs_id": None,
        "time": {"$gt": max_time_airlabs},
        "callsign": {"$in": list(airlabs_dict.keys())}
    }).sort("callsign")

    # Parmi les documents qui matchent :
    list_opensky = list(opensky_matching_callsigns)
    callsigns = list(set([dic['callsign'] for dic in list_opensky]))
    print(f"Nb Callsigns qui matchent : {len(callsigns)}")

    nb_doc = 0
    for callsign in callsigns:
        match = airlabs_dict[callsign]
        match_copy = match.copy()
        airlabs_id = collection_airlabs.insert_one(match_copy).inserted_id
        nb_doc += 1

        # Mettre à jour les document opensky avec le champ airlabs_id
        # {"callsign": callsign, "time": {"$gt": max_time_airlabs}},
        collection_opensky.update_many(
            {"callsign": callsign, "airlabs_id": None},
            {"$set": {"airlabs_id": airlabs_id}}
        )

    print(f"Nb documents Airlabs insérés : {nb_doc}")
    # Supprimer les documents opensky sans airlabs_id
    collection_opensky.delete_many({"airlabs_id": {"$in": [None, ""]}})

    # on ferme la connexion
    client.close()


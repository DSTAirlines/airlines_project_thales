#!/usr/bin/python3
import os
import sys
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")
sys.path.append(f"{parent_dir}/live_api")

# Importer la fonction de connexion à MongoDB
from connection_mongodb import get_connection

# Importer la fonction d'appel à l'API OpenSky
from fetch_opensky_data import query_opensky_api

# CREDENTIALS
USER_OPENSKY_API = os.environ.get("USER_OPENSKY_API")
PASS_OPENSKY_API = os.environ.get("PASS_OPENSKY_API")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")


def get_last_opensky(call_api=False, old_data=None):
    
    # Quand refresh de la page map Dash, appel à l'API OpenSky
    # on ne va garder que les old_data dont le callsign est présent dans le nouvel appel API
    if call_api:
        print("call_api")
        opensky_data = query_opensky_api()
        if old_data:
            old_callsigns = {d["identification"]["callsign"]: d for d in old_data}
            filtered_opensky_data = [data for data in opensky_data if data['callsign'] in old_callsigns]
            return [{'airlabs_doc': old_callsigns[data['callsign']]['static_data'], **data} for data in filtered_opensky_data]

    # A l'ouverture de la page de la map Dash
    # Permet de récupérer les données qui matchent entre data Airlabs et dernier enregistrement OpenSky
    else:
        client = get_connection()
        db = client[MONGO_DB_NAME]
        opensky_collection = db[MONGO_COL_OPENSKY]

        # Recherche du "time" le plus récent
        max_time_result = opensky_collection.find().sort("time", -1).limit(1)
        max_time = max_time_result[0]["time"]

        # Recherche des documents du dernier enregistrement
        pipeline = [
            {"$match": {"time": max_time}},
            {"$lookup": {
                "from": "airlabs",
                "localField": "airlabs_id",
                "foreignField": "_id",
                "as": "airlabs_doc"
            }},
            {"$unwind": "$airlabs_doc"},
            # Forcer l'affichage de tous les champs (pour avoir tous les enregistrements pour la map)
            {"$addFields": {
                "airlabs_doc.aircraft_icao": {"$ifNull": ["$airlabs_doc.aircraft_icao", None]},
                "airlabs_doc.reg_number": {"$ifNull": ["$airlabs_doc.reg_number", None]},
                "airlabs_doc.flag": {"$ifNull": ["$airlabs_doc.flag", None]},
                "airlabs_doc.airline_iata": {"$ifNull": ["$airlabs_doc.airline_iata", None]},
                "airlabs_doc.airline_icao": {"$ifNull": ["$airlabs_doc.airline_icao", None]},
                "airlabs_doc.dep_iata": {"$ifNull": ["$airlabs_doc.dep_iata", None]},
                "airlabs_doc.dep_icao": {"$ifNull": ["$airlabs_doc.dep_icao", None]},
                "airlabs_doc.arr_iata": {"$ifNull": ["$airlabs_doc.arr_iata", None]},
                "airlabs_doc.arr_icao": {"$ifNull": ["$airlabs_doc.arr_icao", None]},
                "airlabs_doc.flight_iata": {"$ifNull": ["$airlabs_doc.flight_iata", None]},
                "airlabs_doc.flight_icao": {"$ifNull": ["$airlabs_doc.flight_icao", None]},
                "airlabs_doc.flight_number": {"$ifNull": ["$airlabs_doc.flight_number", None]},
            }},
        ]

        results = list(opensky_collection.aggregate(pipeline))
        return results

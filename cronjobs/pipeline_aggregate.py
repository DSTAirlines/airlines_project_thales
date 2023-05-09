#!/usr/bin/python3
from datetime import datetime, timedelta
import sys
from pathlib import Path
from pprint import pprint
import os

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

# Se connecter à MongoDB
client = get_connection()
db = client[MONGO_DB_NAME]

opensky = db[MONGO_COL_OPENSKY]

# Pipeline d'aggregation des données
pipeline = [
    {"$match": {"on_ground": False}},
    { "$project": {
        "airlabs_id": 1,
        "time": 1,
        "datatime": 1,
        "callsign": 1,
    }},
    { "$sort":{ "airlabs_id" : 1} },
    { "$group": {
            "_id": "$airlabs_id",
            "callsign": { "$first": "$callsign" },
            "time_start": { "$first" : "$time" },
            "datetime_start": { "$first" : "$datatime" },
            "time_end": { "$last" : "$time" },
            "datetime_end": { "$last" : "$datatime" },
            "count": { "$sum": 1}
        }
    },
    {"$lookup": {
        "from": "airlabs",
        "localField": "_id",
        "foreignField": "_id",
        "as": "airlabs_doc"
    }},
    {"$unwind": "$airlabs_doc"},
    { "$project": {
        "airlabs_id": 1,
        "callsign": 1,
        "time_start": 1,
        "datetime_start": 1,
        "time_end": 1,
        "datetime_end": 1,
        "count": 1,
        "airline_iata": "$airlabs_doc.airline_iata",
        "airline_number": "$airlabs_doc.flight_number",
        "arr_iata": "$airlabs_doc.arr_iata",
        "arr_icao": "$airlabs_doc.arr_icao",
        "dep_iata": "$airlabs_doc.dep_iata",
        "dep_icao": "$airlabs_doc.dep_icao",
        "aircraft_flag": "$airlabs_doc.flag",
        "aircraft_reg_number": "$airlabs_doc.reg_number",
        "aircraft_icao": "$airlabs_doc.aircraft_icao",
    }}
]

results = opensky.aggregate(pipeline)

# Insertion des résultats de la pipeline dans la collection data_aggregated
data_aggregated = db["data_aggregated"]
for result in results:
    data_aggregated.replace_one(
        {"_id": result["_id"]},
        result,
        upsert=True
    )

# Fermeture de la connexion à MongoDB
client.close()



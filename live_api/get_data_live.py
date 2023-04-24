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

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection

# CREDENTIALS
USER_OPENSKY_API = os.environ.get("USER_OPENSKY_API")
PASS_OPENSKY_API = os.environ.get("PASS_OPENSKY_API")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")

def connect():
    client = get_connection()
    db = client[MONGO_DB_NAME]
    opensky_collection = db[MONGO_COL_OPENSKY]
    airlabs_collection = db[MONGO_COL_AIRLABS]

    return opensky_collection, airlabs_collection


def get_last_opensky():

    client = get_connection()
    db = client[MONGO_DB_NAME]
    opensky_collection = db[MONGO_COL_OPENSKY]

    # Recherche du "time" le plus récent
    max_time_result = opensky_collection.find().sort("time", -1).limit(1)
    max_time = max_time_result[0]["time"]

    # Recherche des documents du dernier enregistrement
    pipeline = [
        {"$match": {"time": max_time}},  # Filtrer les documents avec le max_time
        {"$lookup": {
            "from": "airlabs",
            "localField": "airlabs_id",
            "foreignField": "_id",
            "as": "airlabs_doc"
        }},
        {"$unwind": "$airlabs_doc"},
    ]

    result = list(opensky_collection.aggregate(pipeline))

    return result

# result = get_last_opensky()
# print(len(result))
# pprint(result[100])
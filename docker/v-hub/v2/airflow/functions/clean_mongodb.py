#!/usr/bin/python3
from datetime import datetime, timedelta
import sys
from connection_mongodb import get_connection as connexion_mongodb
from pathlib import Path
from pprint import pprint
import os


# CREDENTIALS
KEY_AIRLABS_API = os.environ.get("KEY_AIRLABS_API")
MONGO_DATABASE = os.environ.get("MONGO_INITDB_DATABASE")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
MONGO_COL_STATS = os.environ.get("MONGO_COL_DATA_AGGREGATED")
COLLECTIONS_TO_CLEAN = [MONGO_COL_OPENSKY, MONGO_COL_AIRLABS, MONGO_COL_STATS]

def clean_data():

    # Se connecter à MongoDB
    client = connexion_mongodb()
    db = client[MONGO_DATABASE]

    # Calculer la date limite (7 jours avant aujourd'hui)
    date_limit = datetime.now() - timedelta(days=7)

    # Supprimer les documents de plus de 7 jours dans chaque collection
    for collection_name in COLLECTIONS_TO_CLEAN:
        collection = db[collection_name]
        if collection_name != MONGO_COL_STATS:
            result = collection.delete_many({"datatime": {"$lt": date_limit}})
        else:
            result = collection.delete_many({"datetime_start:": {"$lt": date_limit}})
        print(f"{result.deleted_count} documents supprimés de la collection {collection_name}")

    # Fermer la connexion à MongoDB
    client.close()

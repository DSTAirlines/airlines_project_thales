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
COLLECTIONS_TO_CLEAN = [MONGO_COL_OPENSKY, MONGO_COL_AIRLABS]

# Se connecter à MongoDB
client = get_connection()
db = client[MONGO_DB_NAME]

# Calculer la date limite (10 jours avant aujourd'hui)
date_limit = datetime.now() - timedelta(days=10)

# Supprimer les documents de plus de 10 jours dans chaque collection
for collection_name in COLLECTIONS_TO_CLEAN:
    collection = db[collection_name]
    result = collection.delete_many({"datetime": {"$lt": date_limit}})
    print(f"{result.deleted_count} documents supprimés de la collection {collection_name}")

# Fermer la connexion à MongoDB
client.close()

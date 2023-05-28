#!/usr/bin/python3
import os
import json
from connection_mongodb import get_connection as connect_mongodb
from dotenv import load_dotenv
load_dotenv()


# CREDENTIALS
MONGO_DATABASE = os.environ.get("MONGO_INITDB_DATABASE")
MONGO_COL_STATS = os.environ.get("MONGO_COL_DATA_AGGREGATED")

def init_data():
    
    with open("/app/data_statistics/data.json", "r") as file:
        data = json.load(file)

    if len(data) == 0:
        print("Aucune donnée à insérer")

    else:
        # Se connecter à MongoDB
        client = connect_mongodb()
        db = client[MONGO_DATABASE]

        collection = db[MONGO_COL_STATS]

        if collection.find_one() is None:
            result = collection.insert_many(data)
            print(f"{len(result.inserted_ids)} documents insérés dans la collection {MONGO_COL_STATS}")

        else:
            print("La collection des données statistiques est déjà remplie")

        # Fermer la connexion à MongoDB
        client.close()

#!/usr/bin/python3
import os
import json
from connection_mongodb import get_connection as connect_mongodb
from cron_opensky import query_opensky_api
from cron_airlabs import query_airlabs_api
from dotenv import load_dotenv
load_dotenv()


# CREDENTIALS
MONGO_DATABASE = os.environ.get("MONGO_INITDB_DATABASE")
MONGO_COL_STATS = os.environ.get("MONGO_COL_DATA_AGGREGATED")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")

def init_data():

    # Se connecter à MongoDB
    client = connect_mongodb()
    db = client[MONGO_DATABASE]

    # Test statistics_data
    # --------------------

    # Test présence d'un fichier de data
    if not os.path.exists("/app/data_statistics/data.json"):
        print("Aucun fichier de données à insérer")
        pass
    else:
        with open("/app/data_statistics/data.json", "r") as file:
            data = json.load(file)

        if len(data) == 0:
            print("Aucune donnée à insérer")

        else:
            client = connect_mongodb()
            db = client[MONGO_DATABASE]
            collection = db[MONGO_COL_STATS]

            # Vérif de l'absence de data dans la collection data_aggregated
            if collection.find_one() is None:
                result = collection.insert_many(data)
                print(f"{len(result.inserted_ids)} documents insérés dans la collection {MONGO_COL_STATS}")

            else:
                print("La collection des données statistiques est déjà remplie")

    # Test opensky_data et airlabs_data
    # ---------------------------------

    # opensky_data
    collection_opensky = db[MONGO_COL_OPENSKY]
    collection_airlabs = db[MONGO_COL_AIRLABS]

    if collection_opensky.find_one() is None or collection_airlabs.find_one() is None:
        print(f"Au moins une des collections openSky ou Airlabs est vide")
        collection_opensky.delete_many({})
        collection_airlabs.delete_many({})

        # Appel opensky
        opensky_data = query_opensky_api()
        callsigns_opensky = list(set([dic['callsign'] for dic in opensky_data]))

        # Appel airlabs
        airlabs_data = query_airlabs_api()
        callsigns_airlabs = list(set([dic['flight_icao'] for dic in airlabs_data if dic['flight_icao'] != "" and dic['flight_icao'] is not None]))

        # On ne garde que les callsigns communs aux deux listes
        callsigns = list(set(callsigns_opensky) & set(callsigns_airlabs))

        data_opensky = [dic for dic in opensky_data if dic['callsign'] in callsigns]
        data_airlabs = [dic for dic in airlabs_data if dic['flight_icao'] in callsigns]

        coll_opensky = []
        for callsign in callsigns:
            match_airlabs = [dic for dic in data_airlabs if dic['flight_icao'] == callsign][0]
            match_copy = match_airlabs.copy()
            airlabs_id = collection_airlabs.insert_one(match_copy).inserted_id

            match_opensky = [dic for dic in data_opensky if dic['callsign'] == callsign][0]
            match_copy = match_opensky.copy()
            match_copy['airlabs_id'] = airlabs_id
            coll_opensky.append(match_copy)
        
        collection_opensky.insert_many(coll_opensky)
        print(f"{len(coll_opensky)} documents insérés dans les collections OpenSky et Airlabs")
    
    
    # Fermer la connexion à MongoDB
    client.close()

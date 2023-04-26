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


def get_last_opensky(from_api=False, data_old=None):

    if from_api:
        print(f"from_api: {len(data_old)}")
        print(f"data_old :", data_old[5])
        opensky_data = query_opensky_api()
        if data_old:
            new_data=[]
            all_callsigns = list(op['identification']['callsign'] for op in data_old)
            for data in opensky_data:
                if data['callsign'] in all_callsigns:
                    data_old_flight = [dic for dic in data_old if dic['identification']['callsign'] == data['callsign']]
                    dic = {}
                    dic['airlabs_doc'] = data_old_flight[0]['static_data']
                    for k,v in data.items():
                        dic[k] = v
                    new_data.append(dic)
            print(new_data[:2])
            return new_data

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
        ]

        result = list(opensky_collection.aggregate(pipeline))

        return result
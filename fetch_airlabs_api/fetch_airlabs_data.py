#!/usr/bin/python3
import os
import requests
import time
from pymongo import MongoClient
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/fetch_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection

# CREDENTIALS
KEY_AIRLABS_API = os.environ.get("KEY_AIRLABS_API")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")

def query_opensky_api():

    time_now = int(time.time())
    params = {
        'api_key' : KEY_AIRLABS_API,
    }
    method = 'flights'
    api_base = 'http://airlabs.co/api/v9/'

    response = api_result = requests.get(api_base + method, params)
    result = response.json()
    states = result['response']

    for state in states:
        state['time'] = time_now

    return states

def lauch_script():
    states= query_opensky_api()
    client = get_connection()
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COL_AIRLABS]

    collection.insert_many(states)

lauch_script()

from dotenv import load_dotenv
load_dotenv()
import requests
import json
import os
from math import ceil
from time import sleep
from pprint import pprint


# REFERENCES : STATICS DATA
BASE_URL_REFERENCES = "https://api.lufthansa.com/v1/references/"
ref_endpoints = [
    "countries",
    "cities",
    "airports",
    "airlines",
    "aircraft"
]

# Credentials
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


# GET token from api
def get_token():
    auth_url = "https://api.lufthansa.com/v1/oauth/token"
    auth_payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    auth_response = requests.post(auth_url, data=auth_payload)
    auth_data = auth_response.json()
    access_token = auth_data["access_token"]

    return access_token


# GET metadata from a category
def get_meta(endpoint, base=BASE_URL_REFERENCES):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = base+endpoint+"?limit=1"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Status: success")
        return response.json()
    else:
        raise Exception("Status: error\n"+str(response.status_code)+" "+response.reason)



# GET the number of elements for a category
def get_nb_elements(endpoint):
    meta = get_meta(endpoint)
    if meta is not None:
        for k,v in meta.items():
            return v['Meta']['TotalCount']


# GET all the data of a category from the api
def get_data_from_api(endpoint, base=BASE_URL_REFERENCES):

    # create folder for api results
    path_folder = "datas/"+endpoint
    os.makedirs(path_folder, exist_ok=True)

    # Initial value from limit & offset
    limit = 100
    offset = 0

    # Get number of total values
    nb_elements = get_nb_elements(endpoint)

    # Get the number of iterations
    steps = ceil(nb_elements / 100)

    for step in range(steps):
        sleep(5)
        start = offset
        end = offset + 99 if offset + 99 <= nb_elements else nb_elements - 1
        token = get_token()
        url = base+endpoint

        # define headers & params
        headers = {"Authorization": f"Bearer {token}"}
        params = {"limit": limit, "offset": offset}

        # define & execute the request
        r = requests.get(url, headers=headers, params=params)

        if r.status_code == 200:
            results = r.json()
            path_json = path_folder + "/" + endpoint + "_" + str(start) + "_" + str(end) + ".json"
            with open(path_json, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:
            raise Exception("Error "+str(r.status_code)+" "+r.reason)

        # Set the new offset value
        if end < nb_elements:
            offset = limit + offset


# Get all data in json files
for endpoint in ref_endpoints:
    get_data_from_api(endpoint)

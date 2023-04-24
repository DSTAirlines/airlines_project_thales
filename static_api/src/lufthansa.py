import os
import json
import requests
import pandas as pd
from math import ceil
from time import sleep
from dotenv import load_dotenv

load_dotenv()

# Static data
BASE_URL_REFERENCES = "https://api.lufthansa.com/v1/mds-references/"
ref_endpoints = [
    "countries",
    "cities",
    "airports",
    "airlines",
    "aircraft"
]

# Credentials
CLIENT_ID = os.environ.get("CLIENT_ID_LUFTHANSA")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET_LUFTHANSA")


def get_token():
    """
    Get access token from Lufthansa API.
    Returns:
        str: Access token
    """
    auth_url = "https://api.lufthansa.com/v1/oauth/token"
    auth_payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    auth_response = requests.post(auth_url, data=auth_payload)
    auth_data = auth_response.json()
    return auth_data["access_token"]


def get_meta(endpoint):
    """
    Get metadata from an API category.
    Args:
        endpoint (str): API category
        base (str, optional): Base URL. Defaults to BASE_URL_REFERENCES.
    Returns:
        dict: Metadata JSON response
    """
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = BASE_URL_REFERENCES + endpoint + "?limit=1"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Status: success")
        return response.json()
    else:
        raise Exception(f"Status: error\n{response.status_code} {response.reason}")


def get_nb_elements(endpoint):
    """
    Get the number of elements in a category.
    Args:
        endpoint (str): API category
    Returns:
        int: Total number of elements
    """
    meta = get_meta(endpoint)
    if meta is not None:
        for _, v in meta.items():
            return v['Meta']['TotalCount']
        
def clean_data(items):
    """
    Clean the columns "Names"
    Args:
        data (list): list of dictionnaries
    Returns:
        list: data cleaned
    """
    for item in items:
        if "Names" in item and "Name" in item["Names"]:
            names = item["Names"]["Name"]
            if isinstance(names, list):
                for name in names:
                    if name["@LanguageCode"] == "en" or name["@LanguageCode"] == "EN":
                        item['NameOK'] = name["$"]
            else:
                item['NameOK'] = item["Names"]["Name"]["$"]
        else:
            item['NameOK'] = None
        item.pop('Names')

    return items

def get_data_from_api(endpoint):
    """
    Get all data of a category from the API.
    Args:
        endpoint (str): API category
        base (str, optional): Base URL. Defaults to BASE_URL_REFERENCES.
    """
    # Create array for API results
    data = []
    fails_endpoint = []

    # Create folder "static_results"
    path_folder = "static_results"
    os.makedirs(path_folder, exist_ok=True)

    # Initial values for limit and offset
    limit = 100
    offset = 0

    # Get total number of elements
    nb_elements = get_nb_elements(endpoint)

    # Calculate the number of iterations
    steps = ceil(nb_elements / 100)

    # Get token outside the loop to avoid unnecessary requests
    token = get_token()

    for _ in range(steps):
        sleep(5)

        # Define headers and params
        headers = {"Authorization": f"Bearer {token}"}
        params = {"limit": limit, "offset": offset}

        # Define and execute the request
        url = BASE_URL_REFERENCES + endpoint
        r = requests.get(url, headers=headers, params=params)

        if r.status_code == 200:
            results = r.json()
            resource_key_temp = endpoint[:-3] + "y" if endpoint[-3:] == "ies" else \
                (endpoint[:-1] if endpoint != "aircraft" else endpoint)
            resource_key = f"{resource_key_temp.capitalize()}Resource"
            resource = results[resource_key]
            key1 = next(iter(resource))
            key2 = next(iter(resource[key1]))
            data.extend(resource[key1][key2])
        else:
            fails_endpoint.append(offset)
            print(f"Fail offset {offset} Error {r.status_code} : {r.reason}")

        # Update the offset value
        offset += limit

    # Clean the column "Names"
    data_clean = clean_data(data)

    path_json = f"{path_folder}/{endpoint}.json"
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(data_clean, f, indent=2, ensure_ascii=False)

    return fails_endpoint


# Get all data in json files
fails = {}
for endpoint in ref_endpoints:
    data = get_data_from_api(endpoint)
    if len(data) != 0:
        fails[endpoint] = data

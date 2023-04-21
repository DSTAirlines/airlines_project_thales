import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

# CREDENTIALS
KEY_RAPIDAPI = os.environ.get("KEY_RAPIDAPI")

def get_airport_info(code):
    # BASE URL
    url = "https://airport-info.p.rapidapi.com/airport"

    # PARAMETERS
    if len(code) == 3 or len(code) == 4:
        code_name = "iata" if len(code) == 3 else "icao"
        querystring = {code_name:code}

        headers = {
            "X-RapidAPI-Key": KEY_RAPIDAPI,
            "X-RapidAPI-Host": "airport-info.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)

        if response.status_code == 200:
            print("Status: success")
            return response.json()
        else:
            raise Exception(f"Status: error\n{response.status_code} {response.reason}")
    else:
        raise Exception(f"Code mal formaté")

def get_airline_info(code):
    # BASE URL
    url_base = "https://aviation-reference-data.p.rapidapi.com/airline/"

    # PARAMETERS
    if len(code) == 2 or len(code) == 3:
        url = f"{url_base}{code}"

        headers = {
            "X-RapidAPI-Key": KEY_RAPIDAPI,
            "X-RapidAPI-Host": "aviation-reference-data.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers)

        if response.status_code == 200:
            print("Status: success")
            return response.json()
        else:
            raise Exception(f"Status: error\n{response.status_code} {response.reason}")
    else:
        raise Exception(f"Code mal formaté")

def get_aircraft_type(code):
    # BASE URL
    url = f"https://aviation-reference-data.p.rapidapi.com/icaoType/{code}"

    headers = {
        "X-RapidAPI-Key": KEY_RAPIDAPI,
        "X-RapidAPI-Host": "aviation-reference-data.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code == 200:
        print("Status: success")
        return response.json()
    else:
        raise Exception(f"Status: error\n{response.status_code} {response.reason}")


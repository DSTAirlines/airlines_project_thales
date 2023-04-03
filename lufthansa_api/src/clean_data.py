import json
import pandas as pd
import numpy as np
from os import listdir
from os.path import join, isfile, isdir
from pprint import pprint


def get_languages(dic_languages, languages=["en", "fr"]):
    dic = {}
    if isinstance(dic_languages, list) is False:
        dic_languages = [dic_languages]
    for dic_language in dic_languages:
        if dic_language["@LanguageCode"] in languages:
            lang = dic_language["@LanguageCode"].upper()
            dic[lang] = dic_language["$"]
    return dic

def clean_data_aircrafts(data):
    results = []
    for aircraft in data["AircraftResource"]["AircraftSummaries"]["AircraftSummary"]:
        results.append(aircraft)
    return pd.json_normalize(results)

def clean_data_airports(data):
    results = []
    for airport in data["AirportResource"]["Airports"]["Airport"]:
        airport['Names'] = get_languages(airport["Names"]["Name"])
        results.append(airport)
    return pd.json_normalize(results)

def clean_data_airlines(data):
    results = []
    for airline in data["AirlineResource"]["Airlines"]["Airline"]:
        airline['Names'] = {"EN": airline["Names"]["Name"]["$"]}
        results.append(airline)
    return pd.json_normalize(results)

def clean_data_cities(data):
    results = []
    for city in data["CityResource"]["Cities"]["City"]:
        city['Names'] = get_languages(city["Names"]["Name"])
        results.append(city)
    return pd.json_normalize(results)

def clean_data_countries(data):
    results = []
    for country in data["CountryResource"]["Countries"]["Country"]:
        country['Names'] = get_languages(country["Names"]["Name"])
        results.append(country)
    return pd.json_normalize(results)


def traitement(endpoint):
    results_endpoint = []
    path_folder = "datas/"+endpoint
    files = [f for f in listdir(path_folder) if isfile(join(path_folder, f))]

    for file in files:
        path_file = path_folder + "/" + file
        with open(path_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        match endpoint:
            case "aircraft":
                result = clean_data_aircrafts(data)
            case "airlines":
                result = clean_data_airlines(data)
            case "airports":
                result = clean_data_airports(data)
            case "cities":
                result = clean_data_cities(data)
            case "countries":
                result = clean_data_countries(data)

        results_endpoint.append(result)

    return results_endpoint

def data_to_csv(endpoint):
    path = "datas/csv_cleaned/" + endpoint + "_cleaned.csv"
    data = traitement(endpoint)

    df_data = []
    for df in data:
        df_data.append(df)

    df_endpoint = pd.concat(df_data)
    df_endpoint.to_csv(path, index=False, header=True)


ref_endpoints = [
    "countries",
    "cities",
    "airports",
    "airlines",
    "aircraft"
]

for endpoint in ref_endpoints:
    data_to_csv(endpoint)

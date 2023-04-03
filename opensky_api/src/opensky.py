from opensky_api import OpenSkyApi
import properties as pr
import pandas as pd
import json

def read_json_file(file):
    df = pd.read_json(file)
    df.set_index('ICAO_24', inplace=True)
    print(df)


def query_opensky_api():

    list_state = []
    open_sky_api = OpenSkyApi()

    states = open_sky_api.get_states(bbox=(pr.la_min, pr.la_max, pr.lon_min, pr.lon_max)).states
    for state in states:
        list_state.append({
            "ICAO_24" : state.icao24,
            "ORIGIN_COUNTRY" : state.origin_country,
            "LONGITUDE" : state.longitude,
            "LATITUDE" : state.latitude,
            "ALTITUDE" : state.geo_altitude,
            "VELOCITY" : state.velocity,
            "CAP" : state.true_track,
            "ON_GROUND" : state.on_ground,
        })

    with open(pr.data_filename, 'w+') as file:
        file.write(json.dumps(list_state))
    print('success')

def lauch_script():
    query_opensky_api()
    read_json_file(pr.data_filename)
        
lauch_script()


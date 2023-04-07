from opensky_api import OpenSkyApi
import properties as pr
import pandas as pd
import json

def read_json_file(file):
    df = pd.read_json(file)
    df.set_index('icao_24', inplace=True)
    print(df)


def query_opensky_api():

    list_state = []
    open_sky_api = OpenSkyApi()

    states = open_sky_api.get_states(bbox=(pr.la_min, pr.la_max, pr.lon_min, pr.lon_max)).states
    for state in states:
        list_state.append({
            "icao_24" : state.icao24,
            "origin_country" : state.origin_country,
            "time_position" : state.time_position,
            "last_contact" : state.last_contact,
            "longitude" : state.longitude,
            "latitude" : state.latitude,
            "altitude" : state.geo_altitude,
            "velocity" : state.velocity,
            "cap" : state.true_track,
            "on_ground" : state.on_ground,
        })

    with open(pr.data_filename, 'w+') as file:
        file.write(json.dumps(list_state, indent=3))
    print('success')

def lauch_script():
    query_opensky_api()
    read_json_file(pr.data_filename)
        
lauch_script()


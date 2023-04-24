import pandas as pd
import sys
from pathlib import Path
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash import dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from tabulate import tabulate
from pprint import pprint

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
# Ajout du path des appels API
sys.path.append(f"{parent_dir}/live_api")

# Importer la fonction d'appel à l'API airlabs
from fetch_airlabs_data import lauch_script as airlabs_api

# Importer la fonction de récupération des data
from get_data_live import get_last_opensky

def get_data_live():
    # Appel API AirLabs
    airlabs_api()

    # Récupération data du dernier appel OpenSky
    results = get_last_opensky()

    all_dic = []
    for result in results:
        try:
            dic = {
                'identification': {
                    'fly_id':   result['fly_id'],
                    'callsign': result['callsign'],
                    'icao24':   result['icao_24'],
                    'time':     result['time'],
                    'datatime': result['datatime']
                },
                'static_data': {
                    'aircraft_icao':        result['airlabs_doc']['aircraft_icao'],
                    'aircraft_reg_number':  result['airlabs_doc']['reg_number'],
                    'aircraft_flag':        result['airlabs_doc']['flag'],
                    'airline_iata':         result['airlabs_doc']['airline_iata'],
                    'airline_icao':         result['airlabs_doc']['airline_icao'],
                    'airport_from_iata':    result['airlabs_doc']['dep_iata'],
                    'airport_from_icao':    result['airlabs_doc']['dep_icao'],
                    'airport_arr_iata':     result['airlabs_doc']['arr_iata'],
                    'airport_arr_icao':     result['airlabs_doc']['arr_icao'],
                    'flight_iata':          result['airlabs_doc']['flight_iata'],
                    'flight_icao':          result['airlabs_doc']['flight_icao'],
                    'flight_number':        result['airlabs_doc']['flight_number']
                },
                'dynamic_data': {
                    'baro_altitude':    result['baro_altitude'],
                    'cap':              result['cap'],
                    'geo_altitude':     result['geo_altitude'],
                    'latitude':         result['latitude'],
                    'longitude':        result['longitude'],
                    'status':           result['on_ground'],
                    'velocity':         result['velocity'],
                    'vertical_rate':    result['vertical_rate']
                }
            }
        except Exception as ex:
            # print(ex)
            continue
        all_dic.append(dic)

    print(len(all_dic))
    pprint(all_dic[100])


app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

# Layout de base de l'application
app.layout = html.Div([
    # Avoir le chemin d'accès à l'application 
    dcc.Location(id='url', refresh=False),
    # Contenu de la page à modifier 
    html.Div(id='page-content')
])

# Page d'accueil
index_page = html.Div([
    html.H1("DST Airlines", className="mx-auto text-info mb-4"),
    html.Div([
        dcc.Link("Live Map", href="/live-map", className="mb-3"),
        html.Br(),
        dcc.Link("Search Page", href="/search-page")
    ]),
])

# Page avions en live
live_map = html.Div([
    "Live Map"
])

# Page de recherche dashboard
search_page = html.Div([
    "Search Page"
])

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/live-map":
        get_data_live()
        return live_map
    elif pathname == "/search-page":
        return search_page
    else:
        return index_page

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)

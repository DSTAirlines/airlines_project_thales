import pandas as pd
import sys
from pathlib import Path
import dash
from dash import dcc
from dash import html
import dash_leaflet as dl
from dash import dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from tabulate import tabulate
from pprint import pprint
import dash_extensions as de
import json

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
# Ajout du path des appels API
sys.path.append(f"{parent_dir}/live_api")

# Importer la fonction d'appel à l'API airlabs
from fetch_airlabs_data import lauch_script as airlabs_api

# Importer la fonction de récupération des data
from get_data_live import get_last_opensky


def get_data_live(data=None):
    """
    Retourne les données des vols actuels 
        (data dernier appel OpenSky + data dernier appel Airlabs)
    Args:
        airlabs (bool, optional) Appel à API Airlabs (Default: True)
    Returns:
        Array: Array de dictionnaires de tous les avions en vols
    """
    # print(airlabs)
    # if airlabs:
    #     print("airlabs_api")
    #     # Appel API AirLabs
    #     airlabs_api()

    # Récupération data du dernier appel OpenSky
    if data is None:
        results = get_last_opensky()
    else:
        results = data

    all_dic = []
    for result in results:
        try:
            dic = {
                'identification': {
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
                    'status':           "Au Sol" if result['on_ground'] else "En Vol",
                    'velocity':         result['velocity'],
                    'vertical_rate':    result['vertical_rate']
                }
            }
        except Exception as ex:
            # print(ex)
            continue
        all_dic.append(dic)

    with open("data/live_flights.json", "w", encoding="utf-8") as f:
        json.dump(all_dic, f, indent=2)
    print(len(all_dic))
    return all_dic

data = get_data_live()

def get_data():
    return data

# Retourne le nom des clés (avec espaces et majuscules)
def get_key_name(key):
    return ' '.join(x.capitalize() for x in key.split('_'))

# Callsigns
# def get_all_callsigns(all_callsigns=all_callsigns):
#     try:
#         with open('appli_dash/data/live_flights.json', 'r', encoding='utf-8') as f:
#             data = json.load(f)
#         print(f"Data in get_all_callsigns: {len(data)}") 
#         return list(flight['identification']['callsign'] for flight in data)
#     except:
#         return all_callsigns


def tooltip_content(flight):
    """
    Convertir les data des API en tooltips
    Args:
        flight (dict): Data d'un vol actuel
    Returns:
        Array: Contenu de html.Div des tooltips
    """
    content = [
        html.H5("Infos sur le vol", className="title-tooltip"),
        html.Div([
            html.Span("Callsign : ", className="left-side"),
            html.Span(flight['identification']['callsign'], className="right-side")
        ], style={"whiteSpace": "nowrap"}),
        html.Div([
            html.Span("ICAO : ", className="left-side"),
            html.Span(flight['identification']['icao24'], className="right-side")
        ], style={"whiteSpace": "nowrap"}),
    ]
    dic_static = flight['static_data']
    for k, v in dic_static.items():
        content.append(
            html.Div([
                html.Span(f"{get_key_name(k)} : ", className="left-side"),
                html.Span(v, className="right-side")
            ], style={"whiteSpace": "nowrap"})
        )

    content.append(html.H5("Infos sur la position", className="title-tooltip margin-y-2"))

    dic_dynamic = flight['dynamic_data']
    for k, v in dic_dynamic.items():
        content.append(
            html.Div([
                html.Span(f"{get_key_name(k)} : ", className="left-side"),
                html.Span(v, className="right-side")
            ], style={"whiteSpace": "nowrap"})
        )
    return content


# def generate_detailed_info(flight):
#     return flight["static_data"]["flight_icao"]

# Récupérer les data en json des vols actuels
def get_data_json():
    try:
        with open('data/live_flights.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def create_markers_tooltips(flights):
    """
    Créer les markers et les tooltips
    Args:
        flights (array): Dict des vols actuels
    Returns:
        Array: Tous les dl.DivMarker des avions en vol
    """
    markers = []
    print(f"Flights data in create_markers_tooltips: {len(flights)}")
    # print("Flights data in create_markers_tooltips:", flights)
    for flight in flights:
        latitude = flight["dynamic_data"]["latitude"]
        longitude = flight["dynamic_data"]["longitude"]
        callsign = flight["identification"]["callsign"]
        cap = flight["dynamic_data"]["cap"]
        icon_url = "assets/img/test3.svg"

        html_icon_content = f"""
            <div>
                <img src="{icon_url}" id="plane_{callsign}" style="transform: rotate({cap}deg); width: 15px; height: 20px; background-color: transparent;" />
            </div>
        """

        tooltip = dl.Tooltip(
            html.Div(tooltip_content(flight)),
            className="wrapper-tooltip",
            permanent=False
        )

        markers.append(
            dl.DivMarker(
                id=f"marker_{callsign}",
                position=[latitude, longitude],
                iconOptions={
                    "icon_size": [15, 20],
                    "html": html_icon_content
                },
                children=[tooltip]
            )
        )

    return markers


def display_map(markers_tooltips):
    return html.Div(
        children=[
            dl.Map(
                id="mapLive",
                style={'width': '100%', 'height': '80vh', 'marginBottom': "auto", "marginTop": "0", "display": "block"},
                center=(48.197577, 16.343698),
                zoom=5,
                children=[
                    dl.TileLayer(),
                    *markers_tooltips,
                ],
            ),
            dcc.Interval(
                id='refreshData',
                interval=30*1000,
                n_intervals=0
            ),
            # html.Div(id='clickdata')
        ]
    )


# Création de l'application Dash et de la carte Leaflet
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


# Page de recherche dashboard
search_page = html.Div([
    "Search Page"
])

# # Callback de refresh des data
@app.callback(
    Output("mapLive", "children"),
    [Input("refreshData", "n_intervals")]
)
def update_map(n_intervals):
    # print("Displayed callsigns:", displayed_callsigns)
    data = get_data()
    data_temp = get_last_opensky(from_api=True, data_old=data)
    print(f"data_temp: {len(data_temp)}")
    pprint(data_temp[:2])
    data = get_data_live(data=data_temp)
    print(f"data: {len(data)}")
    markers_tooltips = create_markers_tooltips(data)
    return [
        dl.TileLayer(),
        *markers_tooltips,
    ]

# Callback get marker_id
# @app.callback(Output("clickdata", "children"),
#         [Input(marker.id, "n_clicks") for marker in create_markers_tooltips(get_data_json())])
# def marker_click(*args):
#     marker_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
#     return "Test ID {}".format(marker_id)




@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/live-map":
        markers_tooltips = create_markers_tooltips(data)
        return display_map(markers_tooltips)
    elif pathname == "/search-page":
        return search_page
    else:
        return index_page


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
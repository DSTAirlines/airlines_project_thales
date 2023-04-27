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
from datetime import datetime
import os

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
# Ajout du path des appels API
sys.path.append(f"{parent_dir}/live_api")

# Importer la fonction d'appel à l'API airlabs
from fetch_airlabs_data import lauch_script as airlabs_api

# Importer la fonction de récupération des data
from get_data_live import get_last_opensky



def get_data_live(airlabs=False, data=None):
    """
    Retourne les données des vols actuels 
        (data dernier appel OpenSky + data dernier appel Airlabs)
    Args:
        airlabs (bool, optional) Appel à API Airlabs (Default: False)
            (ne sera appelé que la première fois)
        data (array) Array des dict actuellement affichés (Default: None)
            (pas de data pour le premier appel de la fonction)
    Returns:
        Array: Array de dictionnaires de tous les avions en vols
    """

    if airlabs:
        # Appel API AirLabs
        airlabs_api()

    # Si refresh de la page
    if data:
        dataUpdated = []
        for result in data:
            try:
                flight = {
                    "identification": {
                        "callsign": result["callsign"],
                        "icao24":   result["icao_24"],
                        "time":     result["time"],
                        "datatime": result["datatime"]
                    },
                    "static_data": {
                        "aircraft_icao":        result["airlabs_doc"]["aircraft_icao"],
                        "aircraft_reg_number":  result["airlabs_doc"]["aircraft_reg_number"],
                        "aircraft_flag":        result["airlabs_doc"]["aircraft_flag"],
                        "airline_iata":         result["airlabs_doc"]["airline_iata"],
                        "airline_icao":         result["airlabs_doc"]["airline_icao"],
                        "airport_from_iata":    result["airlabs_doc"]["airport_from_iata"],
                        "airport_from_icao":    result["airlabs_doc"]["airport_from_icao"],
                        "airport_arr_iata":     result["airlabs_doc"]["airport_arr_iata"],
                        "airport_arr_icao":     result["airlabs_doc"]["airport_arr_icao"],
                        "flight_iata":          result["airlabs_doc"]["flight_iata"],
                        "flight_icao":          result["airlabs_doc"]["flight_icao"],
                        "flight_number":        result["airlabs_doc"]["flight_number"]
                    },
                    "dynamic_data": {
                        "baro_altitude":        result["baro_altitude"],
                        "cap":                  result["cap"],
                        "geo_altitude":         result["geo_altitude"],
                        "latitude":             result["latitude"],
                        "longitude":            result["longitude"],
                        "status":               "Au Sol" if result["on_ground"] else "En Vol",
                        "velocity":             result["velocity"],
                        "vertical_rate":        result["vertical_rate"]
                    }
                }
                dataUpdated.append(flight)

            except Exception as ex:
                # print(ex)
                continue

        return dataUpdated

    # Si 1er appel
    else:
        dataInitial = []
        # Récupération data du dernier appel OpenSky
        results = get_last_opensky()
        for result in results:
            try:
                flight = {
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
                        'baro_altitude':        result['baro_altitude'],
                        'cap':                  result['cap'],
                        'geo_altitude':         result['geo_altitude'],
                        'latitude':             result['latitude'],
                        'longitude':            result['longitude'],
                        'status':               "Au Sol" if result['on_ground'] else "En Vol",
                        'velocity':             result['velocity'],
                        'vertical_rate':        result['vertical_rate']
                    }
                }
                dataInitial.append(flight)
            except Exception as ex:
                # print(ex)
                continue

        return dataInitial



# Retourne le nom des clés (avec espaces et majuscules)
def get_key_name(key):
    return ' '.join(x.capitalize() for x in key.split('_'))


# Afficher le datetime du dernier refresh
def datetime_refresh():
    now = datetime.now()
    refresh_time = now.strftime("%d-%m-%Y à %H:%M:%S")
    return html.Div(
        children=f"Last update : {refresh_time}",
        style={
            "position": "absolute",
            "bottom": "12px",
            "left": "15px",
            "backgroundColor": "whitesmoke",
            "padding": "5px",
            "borderRadius": "5px",
            "zIndex": "1000",
        },
        id="datetimeRefresh",
    )


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


def create_markers_tooltips(flights):
    """
    Créer les markers et les tooltips
    Args:
        flights (array): Dict des vols actuels
    Returns:
        Array: Tous les dl.DivMarker des avions en vol
    """
    markers = []
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


def display_map(markers_tooltips, current_data):
    """
    Afficher la map, les markers et les tooltips
    Args:
        markers_tooltips (array):return de create_markers_tooltips()
        current_data (array): Array des dict des data actuels
    Returns:
        Affichage de la map complète
    """
    return html.Div(
        children=[
            dcc.Store(id="current_data", data=current_data),
            html.Div([
                # Espace pour les filtres de la map
            ],
            style = {'width': '100%', 'height': '20vh', 'marginBottom': "auto", "marginTop": "0", "display": "block"}),
            dl.Map(
                id="mapLive",
                style={'width': '100%', 'height': '80vh', 'marginBottom': "0", "marginTop": "auto", "display": "block"},
                center=(46.067314, 4.098643),
                zoom=6,
                children=[
                    datetime_refresh(),
                    dl.TileLayer(),
                    *markers_tooltips,
                ],
            ),
            dcc.Interval(
                id='refreshData',
                interval=30*1000,
                n_intervals=1
            )
        ]
    )


# Variable globale contenant les data
# (à définir avant app)
global_data = None

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
    html.Div([
        html.H1("DST Airlines", className="text-info mb-4 titre-general"),
    ], style={"paddingTop": "5vh"}),

    html.Div([
        dcc.Link("Live Map", href="/live-map", className="mx-3"),
        dcc.Link("Search Page", href="/search-page", className="mx-3"),
        dcc.Link("Statistiques", href="/stats-page", className="mx-3")
    ], className="page-links"),

    html.Div([
        html.H3("Promotion Thales DE Mars 2023", className="h3-index-bottom")
    ], className="container-index-bottom")
], className="main-container index-page")


# Page de recherche dashboard
search_page = html.Div([
    "Search Page"
])


# Page de Statistiques
search_page = html.Div([
    "Search Page"
])


# Callback de refresh des data
@app.callback(
    [Output("mapLive", "children"), Output('current_data', 'data')],
    [Input("refreshData", "n_intervals"),
     Input('current_data', 'data')]
)
def update_map(n_intervals, data):
    global global_data
    if n_intervals > 1:
        data_new_temp = get_last_opensky(call_api=True, old_data=data)
        data_new = get_data_live(airlabs=False, data=data_new_temp)
        markers_tooltips = create_markers_tooltips(data_new)
        return [
            datetime_refresh(),
            dl.TileLayer(),
            *markers_tooltips,
        ], data_new
    
    else:
        markers_tooltips = create_markers_tooltips(global_data)
        return [
            datetime_refresh(),
            dl.TileLayer(),
            *markers_tooltips,
        ], global_data


# Callback get marker_id
# @app.callback(Output("clickdata", "children"),
#         [Input(marker.id, "n_clicks") for marker in create_markers_tooltips(get_data_json())])
# def marker_click(*args):
#     marker_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
#     return "Test ID {}".format(marker_id)


# Callback affichage des pages
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    global global_data
    if pathname == "/live-map":
        if global_data is None:
            global_data = get_data_live(airlabs=True, data=False)
        markers_tooltips = create_markers_tooltips(global_data)
        return display_map(markers_tooltips, global_data)

    elif pathname == "/search-page":
        return search_page

    else:
        return index_page

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")

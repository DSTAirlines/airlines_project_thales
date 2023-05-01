import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
from dash import html
import dash_leaflet as dl
from dash import html
from get_data import *

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
# Ajout des path des fonctions utiles
sys.path.append(f"{parent_dir}/connect_database")
sys.path.append(f"{parent_dir}/live_api")

# Importer la fonction de connexion à db MySQL
from connection_sql import get_connection
# Importer la fonction d'appel à l'API airlabs
from fetch_airlabs_data import lauch_script as airlabs_api


#################################
## UTILITIES FUNCTIONS
#################################

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

# Extraire les données statiques SQL des éléments récupérés par API
def get_static_table(keys_api, key_sql, table, dataStatic):
    lists = []
    for key_api in keys_api:
        list_api = list(set([result['airlabs_doc'].get(key_api) for result in dataStatic if result['airlabs_doc'].get(key_api) is not None]))
        if len(keys_api) > 1:
            lists.append(list_api)
    if len(lists) == 2:
        list_api = list(set(lists[0] + lists[1]))

    engine = get_connection()
    query = f"SELECT * FROM {table}"
    df = pd.read_sql(query, con=engine)
    df = df[df[key_sql].isin(list_api)]
    df = df.reset_index(drop=True)
    df = df.dropna(subset=[key_sql]).drop_duplicates(subset=[key_sql]).reset_index(drop=True)
    df = df.set_index(key_sql, drop=False)
    return df.to_dict('index')


# Traitement affichage tooltip aéroports
def traitement_airport(type_, dic):
    key = 'airport_dep_sql' if type_ == 'dep' else 'airport_arr_sql'
    key_icao = 'airport_from_icao' if type_ == 'dep' else 'airport_to_icao'
    name = dic[key]['airport_name']
    iata = dic[key]['airport_iata']
    icao_test = dic[key]['airport_icao']
    icao = icao_test if icao_test is not None else (dic[key_icao] if dic[key_icao] is not None else "")
    airport_name = f"{name} ({iata}/{icao})" if icao != "" else f"{name} ({iata})"

    city = dic[key]['city_name'] if dic[key]['city_name'] is not None else ""
    country = " - " + dic[key]['country_name'].upper() if dic[key]['country_name'] is not None else ""
    airport_situation = f"{city}{country}"
    airport_flag = dic[key]['country_flag']

    return [airport_name, airport_situation, airport_flag]



#################################
## DASH FUNCTIONS
#################################

def initialize_data():
    """
    Fonction appelée lors du premier appel seulement 
        Récupération data dernier appel OpenSky + data dernier appel Airlabs
        Données splitées en 2:
            - données statiques stockées avec option session de dcc.Store
            - données dynamiques stockées avec option memory de dcc.Store
    Returns:
        Array: 2 arrays (statique & dynamiques) de dict avec infos des vols en direct
    """
    
    # Appel API AirLabs
    #airlabs_api()

    dataDynamic = []
    dataStatic = []

    # Récupération data du dernier appel OpenSky
    results = get_data_initial()

    dic_airports = get_static_table(['dep_iata', 'arr_iata'], 'airport_iata', 'view_airports', results)
    dic_airlines = get_static_table(['airline_iata'], 'airline_iata', 'airlines', results)
    dic_aircrafts = get_static_table(['aircraft_icao'], 'aircraft_icao', 'aircrafts', results)

    for result in results:
        callsign = result['callsign']
        try:
            flight_static = {
                callsign: {
                    'callsign':             callsign,
                    'aircraft_icao':        result['airlabs_doc'].get('aircraft_icao', None),
                    'aircraft_reg_number':  result['airlabs_doc'].get('reg_number', None),
                    'aircraft_flag':        result['airlabs_doc'].get('flag', None),
                    'airline_iata':         result['airlabs_doc'].get('airline_iata', None),
                    'airline_icao':         result['airlabs_doc'].get('airline_icao', None),
                    'airport_from_iata':    result['airlabs_doc'].get('dep_iata', None),
                    'airport_from_icao':    result['airlabs_doc'].get('dep_icao', None),
                    'airport_arr_iata':     result['airlabs_doc'].get('arr_iata', None),
                    'airport_arr_icao':     result['airlabs_doc'].get('arr_icao', None),
                    'flight_iata':          result['airlabs_doc'].get('flight_iata', None),
                    'flight_icao':          result['airlabs_doc'].get('hex', None),
                    'flight_number':        result['airlabs_doc'].get('flight_number', None),
                    'airport_dep_sql':      dic_airports[result['airlabs_doc']['dep_iata']],
                    'airport_arr_sql':      dic_airports[result['airlabs_doc']['arr_iata']],
                    'airline_sql':          dic_airlines[result['airlabs_doc']['airline_iata']],
                    'aircraft_sql':         dic_aircrafts[result['airlabs_doc']['aircraft_icao']]
                }
            }
            dataStatic.append(flight_static)

            flight_dynamic = {
                callsign: {
                    'callsign':             callsign,
                    'time':                 result.get('time'),
                    'datatime':             result.get('datatime'),
                    'baro_altitude':        result.get('baro_altitude'),
                    'cap':                  result.get('cap'),
                    'geo_altitude':         result.get('geo_altitude'),
                    'latitude':             result.get('latitude'),
                    'longitude':            result.get('longitude'),
                    'status':               "Au Sol" if result['on_ground'] else "En Vol",
                    'velocity':             result.get('velocity'),
                    'vertical_rate':        result.get('vertical_rate')
                }
            }
            dataDynamic.append(flight_dynamic)

        except Exception as ex:
            # print(ex)
            continue

    return dataStatic, dataDynamic


def get_data_live(data):
    """
    Retourne les données dynamiques des vols actuels à chaque refresh
        (Appel toutes les 30s à l'API OpenSky)
    Args:
        data (array) Array des dict des data dynamiques actuellement affichés
    Returns:
        Array: Array d'update des data dynamiques des avions en vols
    """

    dataDynamicUpdated = []

    results = get_data_dynamic_updated(data)
    for result in results:
        callsign = result['callsign']
        try:
            flight_dynamic = {
                callsign: {
                    'time':                 result.get('time'),
                    'datatime':             result.get('datatime'),
                    'baro_altitude':        result.get('baro_altitude'),
                    'cap':                  result.get('cap'),
                    'geo_altitude':         result.get('geo_altitude'),
                    'latitude':             result.get('latitude'),
                    'longitude':            result.get('longitude'),
                    'status':               "Au Sol" if result['on_ground'] else "En Vol",
                    'velocity':             result.get('velocity'),
                    'vertical_rate':        result.get('vertical_rate')
                }
            }
            dataDynamicUpdated.append(flight_dynamic)

        except Exception as ex:
            # print(ex)
            continue

    return dataDynamicUpdated



def tooltip_content(flight_data):
    """
    Convertir les data des API en tooltips
    Args:
        flight (dict): Data d'un vol actuel
    Returns:
        Array: Contenu de html.Div des tooltips
    """

    callsign = list(flight_data.keys())[0]
    flight_static = flight_data[callsign]['static_info']
    flight_dynamic = flight_data[callsign]['dynamic_info']

    airport_dep = traitement_airport('dep', flight_static)
    airport_arr = traitement_airport('arr', flight_static)

    airline_name = flight_static['airline_sql'].get('airline_name', '')
    airline_iata = flight_static['airline_sql']['airline_iata']
    airline_icao = flight_static['airline_sql'].get('airline_icao', '')
    airline_txt = f"{airline_name} ({airline_iata} / {airline_icao})"
    vitesse = f"{flight_dynamic['velocity']} m/s" if flight_dynamic['velocity'] is not None else ""
    altitude = f"{flight_dynamic['baro_altitude']} m" if flight_dynamic['baro_altitude'] is not None else ""

    content = [
        html.H5("Infos sur le vol", className="title-tooltip"),

        html.Div([
            html.Span("Numéro de vol : ", className="left-side"),
            html.Span(callsign, className="right-side")
        ], className="margin-y-2"),

        html.Div([
            html.Span("ICAO : ", className="left-side"),
            html.Span(flight_static['flight_icao'], className="right-side")
        ], className="margin-y-2"),

        html.Div([
            html.Span("Compagnie : ", className="left-side-company"),
            html.Span(airline_txt, className="right-side")
        ], className="margin-y-2"),

        html.Div([
            html.Span("Station avion : ", className="left-side"),
            html.Span(flight_dynamic['status'], className="right-side")
        ], className="margin-y-2"),

        html.Div([
            html.Div("Aéroport de départ", style={'textDecoration': 'underline', 'marginBottom': '.2rem'}),
            html.Div(airport_dep[0]),
            html.Div([
                html.Div(airport_dep[1], style={'paddingRight': '1rem', 'paddingTop': '.1rem'}),
                html.Img(src=airport_dep[2], className="img-border")
            ], className="tooltip-flag-display"),
        ], className="margin-y-3"),

        html.Div([
            html.Div("Aéroport d'arrivée", style={'textDecoration': 'underline', 'marginBottom': '.2rem'}),
            html.Div(airport_arr[0]),
            html.Div([
                html.Div(airport_arr[1], style={'paddingRight': '1rem', 'paddingTop': '.1rem'}),
                html.Img(src=airport_arr[2], className="img-border")
            ], className="tooltip-flag-display"),
        ]),
    
        html.H5("Infos sur la position actuelle", className="title-tooltip margin-y-3"),

        html.Div([
            html.Span("Date Time : ", className="left-side"),
            html.Span(flight_dynamic['datatime'], className="right-side")
        ]),

        html.Div([
            html.Span("Altitude : ", className="left-side"),
            html.Span(altitude, className="right-side")
        ]),

        html.Div([
            html.Span("Latitude : ", className="left-side"),
            html.Span(flight_dynamic['latitude'], className="right-side")
        ]),

        html.Div([
            html.Span("Longitude : ", className="left-side"),
            html.Span(flight_dynamic['longitude'], className="right-side")
        ]),

        html.Div([
            html.Span("Vitesse : ", className="left-side"),
            html.Span(vitesse, className="right-side")
        ]),
    ]

    return content


def create_markers_tooltips(static_data, dynamic_data):
    """
    Créer les markers et les tooltips
    Args:
        flights (array): Dict des vols actuels
    Returns:
        Array: Tous les dl.DivMarker des avions en vol
    """
    markers = []
    icon_url = "assets/img/test3.svg"

    callsigns = [list(d.keys())[0] for d in dynamic_data if list(d.keys())[0] is not None]
    static_data_dict = {k: v for dic in static_data for k, v in dic.items()}
    dynamic_data_dict = {k: v for dic in dynamic_data for k, v in dic.items()}

    for callsign in callsigns:
        flight_static = static_data_dict[callsign]
        flight_dynamic = dynamic_data_dict[callsign]

        latitude = flight_dynamic["latitude"]
        longitude = flight_dynamic["longitude"]
        cap = flight_dynamic["cap"]

        html_icon_content = f"""
            <div data-callsign="{callsign}">
                <img src="{icon_url}" id="plane_{callsign}" style="transform: rotate({cap}deg); width: 15px; height: 20px; background-color: transparent;" />
            </div>
        """

        dic_flight = {
            callsign: {
                "static_info":                  flight_static,
                "dynamic_info": {
                        "datatime":             flight_dynamic["datatime"],
                        "baro_altitude":        flight_dynamic["baro_altitude"],
                        "cap":                  cap,
                        "geo_altitude":         flight_dynamic["geo_altitude"],
                        "latitude":             latitude,
                        "longitude":            longitude,
                        "status":               flight_dynamic["status"],
                        "velocity":             flight_dynamic["velocity"],
                        "vertical_rate":        flight_dynamic["vertical_rate"]
                }
            }
        }

        tooltip_hover = dl.Tooltip(f"Flight Number: {callsign}",
            direction="auto",
            permanent=False
        )

        tooltip = dl.Popup(
            html.Div(tooltip_content(dic_flight)),
            className="wrapper-tooltip",
            closeButton=True
        )

        markers.append(
            dl.DivMarker(
                id=f"marker_{callsign}",
                position=[latitude, longitude],
                iconOptions={
                    "icon_size": [15, 20],
                    "html": html_icon_content
                },
                children=[tooltip_hover, tooltip]
            )
        )

    return markers

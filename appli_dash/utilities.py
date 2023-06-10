import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from dash import html
import dash_leaflet as dl
from dash import html
from get_data import *
from sqlalchemy import text
from dash import dcc
import dash_bootstrap_components as dbc
import json
import base64
import dotenv
load_dotenv()

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
def datetime_refresh(nb_planes, n_intervals=False, date_time=''):
    now = datetime.now()
    refresh_time = date_time if date_time else now.strftime("%d-%m-%Y à %H:%M:%S")

    if n_intervals:
        txt_refresh = "Nb de refresh autorisé dépassé"
    else:
        if "UTC" not in refresh_time:
            now_utc = datetime.now(timezone.utc)
            now_utc_str = now_utc.strftime("%H")
            now_local = now_utc.astimezone()
            now_local_str = now_local.strftime("%H")
            if now_utc_str == now_local_str:
                refresh_time += " UTC"
        txt_refresh = f"Last update : {refresh_time} ({nb_planes} vols)"

    return html.Div(
        children=f"{txt_refresh}",
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
    sql = f'''
    SELECT * FROM {table};
    '''
    with engine.connect() as conn:
        query = conn.execute(text(sql))
    df = pd.DataFrame(query.fetchall())
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
            dataDynamicUpdated.append(flight_dynamic)

        except Exception as ex:
            continue

    return dataDynamicUpdated

def tooltip_content_detail(label, value, margin=False):
    """
    Détail d'une row du tooltip
    Args:
        label (str): Label à afficher
        value (str): Value à afficher
        margin (bool, optional): Indique la résence ou non d'une marge (Default: False)
    Returns:
        Balise html.Div de la row du tooltip
    """
    margin_txt = "margin-y-2" if margin else ""
    return html.Div([
        html.Span(f"{label} : ", className="left-side"),
        html.Span(value, className="right-side")
    ], className=margin_txt)


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

        tooltip_content_detail("Numéro de vol", callsign, margin=True),
        tooltip_content_detail("ICAO", flight_static['flight_icao'], margin=True),
        tooltip_content_detail("Compagnie", airline_txt, margin=True),
        tooltip_content_detail("Statut avion", flight_dynamic['status'], margin=True),
        tooltip_content_detail("Type avion", flight_static['aircraft_sql']['aircraft_name'], margin=True),

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

        tooltip_content_detail("Date Time", flight_dynamic['datatime']),
        tooltip_content_detail("Altitude", altitude),
        tooltip_content_detail("Latitude", flight_dynamic['latitude']),
        tooltip_content_detail("Longitude", flight_dynamic['longitude']),
        tooltip_content_detail("Vitesse", vitesse)
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
    icon_url = "assets/img/plane.svg"

    print(f"MAP LIVE - Création des markers et tooltips")

    if dynamic_data is not None and static_data is not None:
        callsigns = [list(d.keys())[0] for d in dynamic_data if list(d.keys())[0] is not None]
        print(f"MAP LIVE - Nombre de callsigns : {len(callsigns)}")

        static_data_dict = {k: v for dic in static_data if dic is not None for k, v in dic.items()}
        dynamic_data_dict = {k: v for dic in dynamic_data if dic is not None for k, v in dic.items()}

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

    return []


def get_from_airports(global_data_static):
    """
    Méthode qui renvoie une liste de dictionnaire des aéroports de départ
    Args: 
        global_data_static: (list) liste de toutes les données statiques des vols sur la Map
    Return:
        Liste des dictionnaires des aéroports de départ
    """
    airports = [{'label': airport[next(iter(airport))]['airport_dep_sql']['airport_name'], 
             'value' : airport[next(iter(airport))]['airport_dep_sql']['airport_name']} for airport in global_data_static]
    
    airports = list({airport['label']: airport for airport in airports}.values())
    airports = sorted(airports, key=lambda x: x['label'])
    return airports

def get_arr_airports(global_data_static):
    """
    Méthode qui renvoie une liste de dictionnaire des aéroports d'arrivé 
    Args: 
        global_data_static: (list) liste de toutes les données statiques des vols sur la Map
    Return:
        Liste des dictionnaires des aéroports d'arrivé
    """
    airports = [{'label': airport[next(iter(airport))]['airport_arr_sql']['airport_name'], 
                 'value' : airport[next(iter(airport))]['airport_arr_sql']['airport_name']} for airport in global_data_static]

    airports = list({airport['label']: airport for airport in airports}.values())
    airports = sorted(airports, key=lambda x: x['label'])
    return airports


def get_countries(global_data_static):
    """
    Méthode qui renvoie une liste de dictionnaire des pays de départ 
    Args: 
        global_data_static: (list) liste de toutes les données statiques des vols sur la Map
    Return:
        Liste des dictionnaires des pays de départ des vols
    """
    countries = [{'label': country[next(iter(country))]['airport_dep_sql']['country_name'], 
                  'value' : country[next(iter(country))]['airport_dep_sql']['country_name']} for country in global_data_static]

    countries = list({country['label']: country for country in countries}.values())
    countries = sorted(countries, key=lambda x: x['label'])
    return countries


def get_airlines(global_data_static):
    """
    Méthode qui renvoie un dictionnaire des compagnies aériennes 
    Args: 
        global_data_static: (list) liste de toutes les données statiques des vols sur la Map
    Return:
        Liste des dictionnaires des compagnies aériennes
    """
    airlines = [{'label': airline[next(iter(airline))]['airline_sql']['airline_name'], 
                 'value' : airline[next(iter(airline))]['airline_sql']['airline_name']} for airline in global_data_static]

    airlines = list({airline['label']: airline for airline in airlines}.values())
    airlines = sorted(airlines, key=lambda x: x['label'])
    return airlines 


def get_filtered_flights(filters, static_flights, dynamic_flights):

    """
    Méthode qui filtre les vols sur la Map suivant les entrées des filtres (Dropdowns)
    Args:
        filters: (dict) le dictionnaire des filtres
        static_flights: (list) la liste des données statiques des vols
        dynamic_flights: (list) la liste des données dynamiques des vols
    Returns:
        filtered_static_flights: (list) la liste des données statiques filtrée
        filtered_dynamic_flights: (list) la liste des données dynamiques filtrée
    """

    filtered_dynamic_flights = []
    test_flight_by_filter = lambda flight_value, filter_value: flight_value == filter_value if filter_value is not None else flight_value

    if filters is not None and any(filter is not None for filter in filters.values()):

        filtered_static_flights = [flight for flight in static_flights if
            (test_flight_by_filter(flight[next(iter(flight))]['airport_dep_sql']['airport_name'], filters['from_airport']))
            and
            (test_flight_by_filter(flight[next(iter(flight))]['airport_arr_sql']['airport_name'], filters['arr_airport']))
            and
            (test_flight_by_filter(flight[next(iter(flight))]['airline_sql']['airline_name'], filters['company']))
            and
            (test_flight_by_filter(flight[next(iter(flight))]['airport_dep_sql']['country_name'], filters['state']))
            and
            (next(iter(flight)) == filters['flight_number'] if filters['flight_number'] not in (None, '') else next(iter(flight)))]

        for dynamic_flight in dynamic_flights:
            if next(iter(dynamic_flight)) in [next(iter(f_flight)) for f_flight in filtered_static_flights]:
                filtered_dynamic_flights.append(dynamic_flight)

        print('static_flights : ', len(filtered_static_flights), 'dynamic_flights : ', len(filtered_dynamic_flights))

    else:
        filtered_static_flights = static_flights
        filtered_dynamic_flights = dynamic_flights

    return filtered_static_flights, filtered_dynamic_flights


def create_dropdown_stats(id, label, options_dict):
    """
    Création de l'affichage des dropdowns de stats du bloc 1
    Args:
        id (str): ID du dropdown
        label (str): Label du dropdown
        options_dict (dict): Dict des options du dropdown
    Returns:
        Div html d'affichage du dropdown
    """
    return html.Div([
        html.P(label, style={'marginTop': '8px', 'marginBottom': '4px'}, className='font-weight-bold'),
        dcc.Dropdown(
            id=id,
            multi=False,
            value=None,
            options=[{'label': options_dict[x], 'value': x} for x in list(options_dict.keys())],
            style={'width': '100%', 'fontSize': '12px'}
        )
    ])


def create_dropdown_callsign(id, label, options_dict=None, multi=False):
    """
    Création de l'affichage des dropdowns de stats du bloc 2
    Args:
        id (str): ID du dropdown
        label (str): Label du dropdown
        options_dict (dict, optionnal): Dict des options du dropdown (par défaut : None)
    Returns:
        Div html d'affichage du dropdown
    """
    if options_dict is None:
        options = []
    else:
        options=[{'label': options_dict[x], 'value': x} for x in list(options_dict.keys())]
    div_dropdown = html.Div([
        html.P(label, style={'marginTop': '8px', 'marginBottom': '4px'}, className='font-weight-bold'),
        dcc.Dropdown(
            id=id,
            multi=multi,
            value=None,
            options=options,
            style={'width': '100%', 'fontSize': '12px'}
        )
    ])
    return div_dropdown


def create_cards_stats(label, value):
    """
    Création de l'affichage des cards de stats du bloc 1
    Args:
        label (str): Label de la card
        value (str): Value de la card (valeur moeyenne pat jour du label)
    Returns:
        html boostrap de l'affichage de la card
    """
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                html.Div([
                    html.H5(label, style={'textAlign': 'center', 'color': 'teal', 'fontSize': '.9rem', 'paddingTop': '.5rem'}),
                    html.H5(value, style={'textAlign': 'center', 'color': 'teal', 'fontSize': '1.3rem'}),
                ]),
            )
        ), width=3,
    )


def create_markers():
    """
    Création des markers aéroports sur la MAP STAT
    """

    AIRPORT_NAME_INDEX = 0
    AIRPORT_IATA_INDEX = 1
    AIRPORT_LATITUDE_INDEX = 2
    AIRPORT_LONGITUDE_INDEX = 3

    engine = connection_mysql()
    sql = """
            SELECT airport_name, airport_iata, airport_latitude, airport_longitude FROM airports 
            WHERE airport_latitude BETWEEN 35.93302587741835 AND 71.40896420697621
            AND airport_longitude BETWEEN -11.360649771804841 AND 32.017698096436696 
            ORDER BY airport_name;
        """

    with engine.connect() as conn:
        query = conn.execute(text(sql))
        airports = query.all()

    markers = []
    icon_url = "assets/img/dot.svg"

    for airport in airports:

        name = airport[AIRPORT_NAME_INDEX]
        iata = airport[AIRPORT_IATA_INDEX]
        latitude = airport[AIRPORT_LATITUDE_INDEX]
        longitude = airport[AIRPORT_LONGITUDE_INDEX]

        html_icon_content = f"""
            <div data-callsign="{iata}">
                <img src="{icon_url}" id="airport_{iata}" style="width: 10px; height: 10px; background-color: transparent;" />
            </div>
        """

        tooltip_hover = dl.Tooltip(name,
            direction="auto",
            permanent=False
        )

        markers.append(
            dl.DivMarker(
                id=f"marker_{iata}",
                position=[latitude, longitude],
                iconOptions={
                    "icon_size": [8, 8],
                    "html": html_icon_content
                },
                children=[tooltip_hover]
            )
        )

    return markers


def create_patterns(airports):
    """
    Création des markers des routes de l'aéroport de départ vers les aéroports les plus désservis.
    """

    patterns = dict(offset='20', endOffset='20', repeat='15', dash=dict(pixelSize=10, pathOptions=dict(color='red', weight=2))),
    multi_pattern =[]

    dep_airport = airports.pop(0)
    for airport in airports:
        positions = [[dep_airport['airport_latitude'], dep_airport['airport_longitude']], [airport['airport_latitude'], airport['airport_longitude']]]
        pattern = dl.PolylineDecorator(positions=positions, patterns=patterns)
        multi_pattern.append(pattern)

    return multi_pattern


def create_flight_markers(flight_positions):
    """
    Création des markers des routes du vol donné par le numéro de vol
    """

    iconUrl = "assets/img/plane.svg"
    marker = dict(rotate=True, markerOptions=dict(icon=dict(iconUrl=iconUrl, iconAnchor=[15, 15])))
    patterns = [dict(repeat='10', dash=dict(pixelSize=5, pathOptions=dict(color='blue', weight=2))),
                dict(offset='10', endOffset='10', repeat='15%', marker=marker)]

    positions = [[flight_position['latitude'], flight_position['longitude']] for flight_position in flight_positions]

    rotated_markers = dl.PolylineDecorator(positions=positions, patterns=patterns)

    return rotated_markers


def encode_credentials(username, password):
    """
    Encode des credentials username et password en chaîne de caractères base64
    """
    username = str(username)
    password = str(password)
    return base64.b64encode(bytes(username + ':' + password, 'utf-8')).decode('utf-8')


def decode_credentials(credentials):
    """
    Decode des credentials base64 en 2 chaines de caractères username et password
    """
    return base64.b64decode(bytes(credentials, 'utf-8')).decode('utf-8').split(':')


def get_encoded_credentials_admin():
    username = os.environ.get('ADMIN_LOGIN_API')
    password = os.environ.get('ADMIN_PASSWORD_API')
    return encode_credentials(username, password)

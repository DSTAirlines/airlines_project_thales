import pandas as pd
import dash
from dash import dcc
from dash import html
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from tabulate import tabulate
from pprint import pprint
import dash_extensions as de
import pandas as pd
from utilities import *
from get_data import *
from dash.exceptions import PreventUpdate


def display_map(markers_tooltips):
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
            dcc.Store(id="dynamicData", storage_type="memory"),
            dcc.Store(id="staticData", storage_type="session"),
            html.Div([
                html.Div(style = {'width': '100%', 'height': '20vh', 'marginBottom': "auto", "marginTop": "0", 
                              "display": "flex", 'justify-content':'center', 'align-items':'center', 'backgroundColor':'#ECEFF1'}, 
                     children=[
                dcc.Store(id='filters', storage_type='memory'),
                dcc.Store(id='filtered_flights', storage_type='memory'),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label('Aéroport de départ:', html_for='departure_airport'),
                    dcc.Dropdown(id='departure_airport', options = get_airports(), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Aéroport d'arrivé :", html_for='arrival_airport'),
                    dcc.Dropdown(id='arrival_airport', options = get_airports(), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Compagnie aérienne :", html_for='airline_company'),
                    dcc.Dropdown(id='airline_company', options = get_airlines(), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Pays d'origine :", html_for='state_registration'),
                    dcc.Dropdown(id='state_registration', options = get_countries(), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block'}, children=[
                    dbc.Label('Numéro de vol :'),
                    dbc.Input(id="flight_number", placeholder="Entrer un numéro de vol...", type="text")
                ]),
                html.Div(style={'marginTop':'32px'}, children=[
                    dbc.Button('FILTRER', id='filter_button')])
                ])
            ]),
            dl.Map(
                id="mapLive",
                style={'width': '100%', 'height': '80vh', 'marginBottom': "0", "marginTop": "auto", "display": "block"},
                center=(46.067314, 4.098643),
                zoom=6,
                children=[
                    datetime_refresh(),
                    dl.TileLayer(),
                    *markers_tooltips,
                ]
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
global_data_dynamic = None
global_data_static = None
global_launch_flag = True

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


# Callback load de la page
@app.callback(
    Output('staticData', 'data'),
    Input('staticData', 'data')
)
def init_static(static_data):
    global global_data_static
    if static_data is None:
        return global_data_static


# Callback de refresh des data
@app.callback(
    [Output("mapLive", "children"), 
     Output('dynamicData', 'data')],
    [Input("refreshData", "n_intervals"),
     Input('dynamicData', 'data'),
     Input('staticData', 'data'),
     State('filters', 'data')]
)
def update_map(n_intervals, data_dyn, data_stat, filters):
    global global_data_dynamic

    # Ajout d'une sécutité en cas d'oubli de fermeture du script
    if n_intervals <= 20:

        # Script d'update
        if data_dyn is None:
            global_data_dynamic = get_data_live(global_data_dynamic)
        else:
            global_data_dynamic = get_data_live(data_dyn)

        data_stat = get_filtered_static_flights(filters, data_stat)
        data_dyn = get_filtered_dynamic_flights(filters, data_stat, global_data_dynamic)

        # data_new = get_data_live(data_new_temp)
        markers_tooltips = create_markers_tooltips(data_stat, data_dyn)
        return [
            datetime_refresh(),
            dl.TileLayer(),
            *markers_tooltips,
        ], global_data_dynamic


# Callback des filtres
@app.callback(
        Output('filters', 'data'),
        [Input('departure_airport', 'value'),
         Input('arrival_airport', 'value'),
         Input('airline_company', 'value'),
         Input('state_registration', 'value'),
         Input('flight_number', 'value')
         ]
)
def filters(from_airport, arr_airport, company, state, flight_number):
    """
    Enregistre les filtres entrés dans un dictionnaire pour filtrage des vols
    Args:
        from_airport: aéroport de départ
        arr_airport: aéroport d'arrivé
        company: compagnie aérienne de l'aéronef
        state: pays d'origine de l'aéronef
        flight_number: numéro de vol de l'aéronef
    Return:
        filters: le dictionnaire des filtres
    """
    
    filters = {
        'from_airport': from_airport,
        'arr_airport': arr_airport,
        'company': company,
        'state': state,
        'flight_number': flight_number,
    }

    return filters

# Callback du bouton de filtre
@app.callback(
        Output("mapLive", "children", allow_duplicate=True),
        [Input('filter_button', 'n_clicks'),
         State('staticData', 'data'),
         State('dynamicData', 'data'),
         State('filters', 'data'),
         State('datetimeRefresh', 'children')
         ],
         prevent_initial_call=True
)
def filter_button(click, static_data, dynamic_data, filters, date_time):
    """
    Filtres les vols sur la Map suivant la valeurs des filtres
    Args:
        click: event click sur le bouton 'FILTRER'
        filters (dict): dictionnaire des filtres choisis par l'utilisateur
        flights (array): Array de tous les vols avant filtrage
    Return:
        filtered_flights (array): Array de tous les vols après filtrage
    """
    if click is None:
        raise PreventUpdate
    
    else:
        filtered_flights_stat = get_filtered_static_flights(filters, static_data)
        filtered_flights_dynamic = get_filtered_dynamic_flights(filters, filtered_flights_stat, dynamic_data)
        filtered_markers_tooltips = create_markers_tooltips(filtered_flights_stat, filtered_flights_dynamic)
        date_time = date_time.strip('Last update : ')
        
        return [datetime_refresh(date_time), dl.TileLayer(), *filtered_markers_tooltips]

def get_filtered_static_flights(filters, flights):

    test_flight_by_filter = lambda flight_value, filter_value: flight_value == filter_value if filter_value is not None else flight_value

    if any(filter is not None for filter in filters.values()):

        filtered_flights = [flight for flight in flights if
            (test_flight_by_filter(flight[next(iter(flight))]['airport_from_iata'], filters['from_airport']))
             and
            (test_flight_by_filter(flight[next(iter(flight))]['airport_arr_iata'], filters['arr_airport']))
             and
            (test_flight_by_filter(flight[next(iter(flight))]['airline_iata'], filters['company']))
            and
            (test_flight_by_filter(flight[next(iter(flight))]['aircraft_flag'], filters['state']))
            and
            (next(iter(flight)) == filters['flight_number'] if filters['flight_number'] not in (None, '') else next(iter(flight)))]
            # (flight[next(iter(flight))]['flight_number'] == filters['flight_number'] if filters['flight_number'] not in (None, '') else flight[next(iter(flight))]['flight_number'])]

        print(len(filtered_flights))
    else:
        filtered_flights = flights
    
    return filtered_flights

def get_filtered_dynamic_flights(filters, filtered_flights, dynamic_flights):

    filtered_dynamic_flights = []
    if any(filter is not None for filter in filters.values()):
        for dynamic_flight in dynamic_flights:
            for filtered_flight in filtered_flights:
                if next(iter(dynamic_flight)) == next(iter(filtered_flight)):
                    filtered_dynamic_flights.append(dynamic_flight)
    
        print(len(filtered_dynamic_flights))

    else:
        filtered_dynamic_flights = dynamic_flights
    
    return filtered_dynamic_flights



# Callback affichage des pages
@app.callback(
    Output("page-content", "children"), 
    [Input("url", "pathname")]
)
def display_page(pathname):
    global global_data_static
    global global_data_dynamic
    if pathname == "/live-map":
        if global_data_static is None:
            global_data_static, global_data_dynamic = initialize_data()
        markers_tooltips = create_markers_tooltips(global_data_static, global_data_dynamic)
        return display_map(markers_tooltips)

    elif pathname == "/search-page":
        return search_page

    else:
        return index_page

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")

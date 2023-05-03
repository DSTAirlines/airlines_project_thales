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


def display_map(markers_tooltips, nb_planes):
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
                              "display": "flex", 'justifyContent':'center', 'alignItems':'center', 'backgroundColor':'#ECEFF1'}, 
                     children=[
                dcc.Store(id='filters', storage_type='memory'),
                dcc.Store(id='filtered_flights', storage_type='memory'),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label('Aéroport de départ:', html_for='departure_airport'),
                    dcc.Dropdown(id='departure_airport', options = get_from_airports(global_data_static), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Aéroport d'arrivé :", html_for='arrival_airport'),
                    dcc.Dropdown(id='arrival_airport', options = get_arr_airports(global_data_static), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Compagnie aérienne :", html_for='airline_company'),
                    dcc.Dropdown(id='airline_company', options = get_airlines(global_data_static), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Pays de départ :", html_for='state_registration'),
                    dcc.Dropdown(id='state_registration', options = get_countries(global_data_static), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block'}, children=[
                    dbc.Label('Numéro de vol :'),
                    dbc.Input(id="flight_number", placeholder="Entrer un numéro de vol...", type="text",
                              style={'textTransform': 'uppercase'}, value=None)
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
                    datetime_refresh(nb_planes),
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
        dcc.Link("Interactive Live Map", href="/live-map", className="mx-3"),
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
    if n_intervals <= 15:

        # Script d'update
        if data_dyn is None:
            global_data_dynamic = get_data_live(global_data_dynamic)
        else:
            global_data_dynamic = get_data_live(data_dyn)

        static_datas, dynamic_datas = get_filtered_flights(filters, data_stat, global_data_dynamic)

        markers_tooltips = create_markers_tooltips(static_datas, dynamic_datas)
        nb_planes = len(global_data_dynamic)
        return [
            datetime_refresh(nb_planes),
            dl.TileLayer(),
            *markers_tooltips,
        ], global_data_dynamic

    else:
        markers_tooltips = create_markers_tooltips(data_stat, data_dyn)
        nb_planes = len(data_dyn)
        return [
            datetime_refresh(nb_planes, n_intervals=True),
            dl.TileLayer(),
            *markers_tooltips,
        ], data_dyn


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
        'flight_number': flight_number.upper() if flight_number is not None else flight_number if flight_number != '' else None,
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
    Filtre les vols sur la Map suivant la valeur des filtres
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
        filtered_static_flights, filtered_dynamic_flights = get_filtered_flights(filters, static_data, dynamic_data)
        filtered_markers_tooltips = create_markers_tooltips(filtered_static_flights, filtered_dynamic_flights)
        date_time = date_time.strip('Last update : ')
        print(date_time)
        nb_planes = len(filtered_dynamic_flights)
        
        return [datetime_refresh(nb_planes, date_time), dl.TileLayer(), *filtered_markers_tooltips]

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
        nb_planes = len(global_data_dynamic)
        return display_map(markers_tooltips, nb_planes)

    elif pathname == "/search-page":
        return search_page

    else:
        return index_page

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")

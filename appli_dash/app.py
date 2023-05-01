import pandas as pd
import dash
from dash import dcc
from dash import html
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from tabulate import tabulate
from pprint import pprint
import dash_extensions as de
import pandas as pd
from utilities import *
from get_data import *


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
     Input('staticData', 'data')]
)
def update_map(n_intervals, data_dyn, data_stat):
    global global_data_dynamic

    # Ajout d'une sécutité en cas d'oubli de fermeture du script
    if n_intervals <= 10:

        # Script d'update
        if data_dyn is None:
            global_data_dynamic = get_data_live(global_data_dynamic)
        else:
            global_data_dynamic = get_data_live(data_dyn)

        # data_new = get_data_live(data_new_temp)
        markers_tooltips = create_markers_tooltips(data_stat, global_data_dynamic)
        return [
            datetime_refresh(),
            dl.TileLayer(),
            *markers_tooltips,
        ], global_data_dynamic


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

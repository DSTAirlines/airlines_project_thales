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
from datetime import date


################################################################################################
## LAYOUT PAGE D'ACCUEIL
################################################################################################
index_page = html.Div([
    html.Div([
        html.H1("DST Airlines", className="text-info mb-4 titre-general"),
    ], style={"paddingTop": "5vh"}),

    html.Div([
        dcc.Link("Live Map", href="/live-map", className="mx-3"),
        dcc.Link("Data Stats", href="/stats-page", className="mx-3"),
        dcc.Link("Map Stats", href="/stats-map-page", className="mx-3"),
    ], className="page-links"),

    html.Div([
        html.H3("Promotion Thales DE Mars 2023", className="h3-index-bottom")
    ], className="container-index-bottom")
], className="main-container index-page")


################################################################################################
## LAYOUT PAGE MAP-LIVE
################################################################################################

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
                html.Div(style = {'width': '100%', 'height': '12vh', 'marginBottom': "auto", "marginTop": "0", 
                              "display": "flex", 'justifyContent':'center', 'alignItems':'center', 'backgroundColor':'#ECEFF1'}, 
                     children=[
                dcc.Store(id='filters', storage_type='memory'),
                dcc.Store(id='filtered_flights', storage_type='memory'),
                html.Div(nav(), className="marges-navbar-map", style={'display': 'inline-block', 'width': '10%'}),
                html.Div(className="mx-3, py-2", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label('Aéroport de départ:', html_for='departure_airport'),
                    dcc.Dropdown(id='departure_airport', options = get_from_airports(global_data_static), value=None, style={'fontSize': '12px'})
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Aéroport d'arrivé :", html_for='arrival_airport'),
                    dcc.Dropdown(id='arrival_airport', options = get_arr_airports(global_data_static), value=None, style={'fontSize': '12px'})
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Compagnie aérienne :", html_for='airline_company'),
                    dcc.Dropdown(id='airline_company', options = get_airlines(global_data_static), value=None)
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dbc.Label("Pays d'origine :", html_for='state_registration'),
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
                style={'width': '100%', 'height': '88vh', 'marginBottom': "0", "marginTop": "auto", "display": "block"},
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


################################################################################################
## LAYOUT PAGE STATS
################################################################################################

def display_stats_page(df):
    """
    Afficher la page de statistiques
    Args:
        df (dataframe): dataframe des données
    Returns:
        Affichage de la page de statistiques
    """

    # Récupération des données
    stats_by_day =  get_global_stats(df)
    dates = list(stats_by_day.index)
    dates_str = [x.strftime("%d-%m-%Y") for x in dates]
    synthese_values = []
    for col in ['callsign', 'airline_iata', 'dep_iata', 'arr_iata']:
        synthese_values.append(round(stats_by_day[col].mean()))
    
    # dic dropdown bloc 1
    dic_airlines = get_drop_dic_individual_stats('airline_iata', 'airline_name', df)
    dic_dep_airports = get_drop_dic_individual_stats('dep_iata', 'dep_airport_name', df)
    dic_arr_airports = get_drop_dic_individual_stats('arr_iata', 'arr_airport_name', df)
    dic_aircrafts = get_drop_dic_individual_stats('aircraft_icao', 'aircraft_name', df)

    # dic dropdown bloc 2
    dic_callsign_dep_airports = get_dropdown_callsigns_aiprorts_dep(df)


    # SideBar avec dropdowns
    # ----------------------
    sidebar = html.Div([
        dbc.Row(
            [
                dbc.Col(nav('dropdown-absolute'), width=11),
            ],
            style={"height": "5vh"}
        ),
        dbc.Row(
            [
                html.P('Choix des paramètres', style={'marginTop': '2rem', 'textTransform': 'underline', 'fontSize': '1.2rem', 'fontWeight': 'bold'}),

                create_dropdown_stats('dropdown-airline', 'Compagnies', dic_airlines),
                create_dropdown_stats('dropdown-dep-airport', 'Aéroports de départ', dic_dep_airports),
                create_dropdown_stats('dropdown-arr-airport', "Aéroports d'arrivée", dic_arr_airports),
                create_dropdown_stats('dropdown-aircraft', "Type d'avion", dic_aircrafts),
            ],
            className='d-block color-dark',
            style={"height": "46vh"}
        ),
        dbc.Row(
            [
                html.Hr(),
                html.P('Trouver un vol', style={'marginTop': '2rem', 'textTransform': 'underline', 'fontSize': '1.2rem', 'fontWeight': 'bold'}),
                create_dropdown_callsign('dropdown-callsign-dep', 'Aéroport de départ', dic_callsign_dep_airports),
                create_dropdown_callsign('dropdown-callsign-arr', 'Aéroport d\'arrivée'),
                create_dropdown_callsign('dropdown-callsign-num', 'Numero de vol'),
            ],
            className='d-block',
            style={"height": "45vh"}
        )],
        className='bg-secondary text-white px-3'
    )

    # Content avec 3 parties différentes
    # ----------------------------------
    content = html.Div([
        dbc.Row(
            [
                # Partie 1: Affichage du graphique des statistiques journalières agrégées
                dbc.Col(
                    [
                        html.Div([
                            dcc.Graph(
                                id='example-graph',
                                figure={
                                    'data': [
                                        go.Scatter(x=dates_str, y=stats_by_day['callsign'], 
                                            name='Vols', yaxis='y1', mode='lines+markers', marker=dict(color='blue'), fill='tozeroy'),
                                        go.Scatter(x=dates_str, y=stats_by_day['airline_iata'], 
                                            name='Compagnies', yaxis='y2', mode='lines+markers', marker=dict(color='green')),
                                        go.Scatter(x=dates_str, y=stats_by_day['dep_iata'], 
                                            name='Aéroports de départ', yaxis='y2', mode='lines+markers', marker=dict(color='red')),
                                        go.Scatter(x=dates_str, y=stats_by_day['arr_iata'], 
                                            name='Aéroports d\'arrivée', yaxis='y2', mode='lines+markers', marker=dict(color='purple'))
                                    ],
                                    'layout': go.Layout(
                                        margin={'l': 40, 'b': 100, 't': 80, 'r': 40},
                                        title={
                                            'text': 'Statistiques par jour',
                                            'font': {'size': 16, 'color': 'teal'},
                                            'x': 0.065,
                                            'y': 0.96,
                                            'xanchor': 'left'
                                        },
                                        xaxis={'gridcolor': '#e3e3e3', 'tickformat': '%d-%m-%Y', 'nticks': len(stats_by_day.index)},
                                        yaxis={'title': 'Vols', 'side': 'left', 'gridcolor': '#e3e3e3', 'titlefont': {'color': 'blue'}, 'tickfont': {'color': 'blue'}},
                                        yaxis2={'title': 'Autres variables', 'overlaying': 'y', 'side': 'right', 'gridcolor': '#e3e3e3', 'titlefont': {'color': 'green'}, 'tickfont': {'color': 'green'}},
                                        legend={'x': 0.2, 'y': 1.1, 'orientation': 'h', 'bgcolor': 'rgba(255, 255, 255, 0.5)', 'font': {'size': 12}},
                                        # legend={'x': 1.2, 'y': 1, 'bgcolor': 'rgba(255, 255, 255, 0.5)', 'bordercolor': 'black', 'borderwidth': 1, 'font': {'size': 10}},
                                        plot_bgcolor='rgba(237, 248, 251, 0.9)',
                                        paper_bgcolor='rgba(255, 255, 255, 0.1)'
                                    )
                                },
                            )
                        ], style={'height': '85%'}),
                        dbc.Row(
                            [
                                create_cards_stats('Vols', synthese_values[0]),
                                create_cards_stats('Compagnies', synthese_values[1]),
                                create_cards_stats('Aéroports Départ', synthese_values[2]),
                                create_cards_stats('Aéroports Arrivée', synthese_values[3]),
                            ],
                            # style={"height": "6vh"}
                        ),
                    ],
                    style={"height": "49vh"},
                    className='bg-light'
                ),

                # Partie 2: Affichage du tableau des statistiques individuelles (choix par dropdowns)
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.Span('Détails d\'un élément ', style={'marginTop': '1rem', 'color': '#72ffff'}),
                            html.Span(id='titre-detail-complement', style={'marginTop': '1rem', 'color': '#72ffff'}),
                        ],
                        style={'display': 'flex'}
                        ),
                        html.Div(id='complement-dropdown', className='complement-dropdown'),
                    ]),
                    html.Div(id='resultDropdown', style={'marginTop': '1.5rem'}),
                ],
                # className='bg-light pl-3'
                className='bg-dark text-white pl-3'
                )
            ],
            style={"height": "49vh"}),

        # Partie 3: Affichage du tableau des vols (durée, details pour un callsign particulier)
        dbc.Row([
                dbc.Col(
                    [
                        html.Div(id='result-callsign', style={'marginTop': '3.5rem'}),
                    ],
                    className='bg-light'
                    )
            ],
            style={"height": "50vh"}
            )
        ]
    )

    # Ensemble de la page
    # -------------------
    return dbc.Container([
        dcc.Store(id="dic-dropdown-airport", storage_type="memory"),
        dbc.Row([
                dbc.Col(sidebar, width=2, className='bg-light px-0'),
                dbc.Col(content, width=10)
            ],
            style={"height": "100vh", "width": "100%"}
        )],
    fluid=True
    )


################################################################################################
## LAYOUT STAT MAP PAGE
################################################################################################

def display_stat_map(markers):

    return html.Div(
        children=[
            html.Div([
                html.Div(style = {'width': '100%', 'height': '20vh', 'marginBottom': "auto", "marginTop": "0", 
                              "display": "flex", 'justifyContent':'center', 'alignItems':'center', 'backgroundColor':'#ECEFF1'}, 
                     children=[
                html.Div(nav(), className="marges-navbar-map", style={'display': 'inline-block', 'width': '10%'}),
                html.Div(className="mx-3 py-2", style={'display': 'inline-block'}, children=[
                    dcc.Store(id='date_stat', storage_type='memory'),
                    dbc.Label('Date :', html_for='date', style={'display':'block'}),
                    dcc.DatePickerSingle(id='date_picker', 
                                         month_format='DD-MM-YYYY',
                                         display_format='DD/MM/YYYY',
                                         clearable=True,
                                         min_date_allowed = date(2023, 1, 1), max_date_allowed = date(2023, 6, 30), 
                                         initial_visible_month = date.today(),
                                         style={'zIndex':100000, 'position':'relative'})
                ]),
                html.Div(className="mx-3", style={'display': 'inline-block', 'width': '15%'}, children=[
                    dcc.Store(id='dep_airport_data', storage_type='memory'),
                    dbc.Label("Aéroport de départ :", html_for='arrival_airport'),
                    dcc.Dropdown(id='dep_airport_stat', options = get_airports(), value=None, style={'fontSize': '12px'})
                ]), 
                html.Div(className="mx-3", style={'display': 'inline-block'}, children=[
                    dcc.Store(id='flight_number_data', storage_type='memory'),
                    dbc.Label('Numéro de vol :'),
                    dbc.Input(id="flight_number_stat", placeholder="Entrer un numéro de vol...", type="text",
                              style={'textTransform': 'uppercase'}, value=None)
                ]),
                html.Div(style={'marginTop':'32px'}, children=[
                    dbc.Button('ROUTES', id='routes_button')])
                ])
            ]),
            dl.Map(
                id="mapStat",
                style={'width': '100%', 'height': '80vh', 'marginBottom': "0", "marginTop": "auto", "display": "block"},
                center=(46.067314, 4.098643),
                zoom=6,
                children=[
                    dl.TileLayer(),
                    *markers
                ]
            )
        ]
    )

################################################################################################
## NAVIGATION PAGE
################################################################################################

def nav(classes=""):
    """
    Afficher la barre de navigation
    Args:
        class (str):classe de la barre de navigation
    Returns:
        Affichage de la barre de navigation
    """

    return dbc.DropdownMenu(
        label="Menu",
        color="info",
        children=[
            dbc.DropdownMenuItem("Index", href="/"),
            dbc.DropdownMenuItem("Map Live", href="/live-map"),
            dbc.DropdownMenuItem("Statistics Data", href="stats-page"),
            dbc.DropdownMenuItem("Statistics Map", href="stats-map-page"),
        ],
        nav=True,
        in_navbar=True,
        id="menuDropdown",
        className=classes
    ) 


################################################################################################
## APPLICATION DASH
################################################################################################

# Variable globale contenant les data
# (à définir avant app)
global_data_dynamic = None
global_data_static = None
global_launch_flag = True
global_statistics_df = None
global_n_intervals_map = None

# Création de l'application Dash et de la carte Leaflet
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

# Layout de base de l'application
# -------------------------------
app.layout = html.Div([
    # Avoir le chemin d'accès à l'application 
    dcc.Location(id='url', refresh=False),
    # Contenu de la page à modifier 
    html.Div(id='page-content')
])


################################################################################################
## CALLBACK LOAD DES PAGES
################################################################################################

# Load page "live-map"
# --------------------
@app.callback(
    Output('staticData', 'data'),
    [Input("url", "pathname"),
    Input('staticData', 'data')]
)
def init_static(pathname, static_data):
    global global_data_static
    if pathname == "/live-map":
        if static_data is None:
            return global_data_static
    return None


################################################################################################
## CALLBACK AFFICHAGE DES PAGES
################################################################################################
@app.callback(
    Output("page-content", "children"), 
    [Input("url", "pathname")]
)
def display_page(pathname):
    global global_data_static
    global global_data_dynamic
    global global_statistics_df

    # Page "live-map"
    if pathname == "/live-map":
        print("MAP LIVE - STEP 1 : Initialisation des données static et dynamic")
        if global_data_static is None or global_data_dynamic is None:
            global_data_static, global_data_dynamic = initialize_data()
        print(f"MAP LIVE - STEP 1 - len de global_data_static : {len(global_data_static)}")
        print(f"MAP LIVE - STEP 1 - len de global_data_dynamic : {len(global_data_dynamic)}")
        print(len(global_data_dynamic))
        markers_tooltips = create_markers_tooltips(global_data_static, global_data_dynamic)
        nb_planes = len(global_data_dynamic)
        return display_map(markers_tooltips, nb_planes)

    # Page "stats-page"
    elif pathname == "/stats-page":
        global_data_dynamic = None
        if global_statistics_df is None:
            global_statistics_df = get_data_statistics()
        return display_stats_page(global_statistics_df)
    
    elif pathname == '/stats-map-page':
        markers = create_markers()
        return display_stat_map(markers)

    else:
        return index_page


################################################################################################
## CALLBACK PAGE LIVE MAP - REFRESH DES DATA
################################################################################################
@app.callback(
    [Output("mapLive", "children"), 
     Output('dynamicData', 'data')],
    [Input("refreshData", "n_intervals"),
     Input('dynamicData', 'data'),
     Input('staticData', 'data'),
     State('filters', 'data'),
     Input('url', 'pathname')]
)
def update_map(n_intervals, data_dyn, data_stat, filters, pathname):
    global global_data_dynamic
    global global_n_intervals_map
    print("MAP LIVE - STEP 3 - Update map")
    print(f"MAP LIVE - STEP 3 - n_intervals: {n_intervals}")

    # if global_n_intervals_map is None:
    #     global_n_intervals_map = n_intervals
    # else:
        # if global_n_intervals_map != n_intervals:
    if pathname == "/live-map":
        global_n_intervals_map = n_intervals
        old_data_dyn = global_data_dynamic
        if data_dyn is not None:
            old_data_dyn = get_data_live(data_dyn)

        # Ajout d'une sécutité en cas d'oubli de fermeture du script
        if n_intervals <= 15:
        
            # Script d'update
            static_datas, global_data_dynamic = get_filtered_flights(filters, data_stat, old_data_dyn)

            markers_tooltips = create_markers_tooltips(static_datas, global_data_dynamic)
            nb_planes = len(global_data_dynamic)
            return [
                datetime_refresh(nb_planes),
                dl.TileLayer(),
                *markers_tooltips,
            ], global_data_dynamic

        else:
            markers_tooltips = create_markers_tooltips(data_stat, old_data_dyn)
            nb_planes = len(old_data_dyn)
            return [
                datetime_refresh(nb_planes, n_intervals=True),
                dl.TileLayer(),
                *markers_tooltips,
            ], old_data_dyn
    else:
        return [], None


# Callback pour mettre à jour l'intervalle du refresh en fonction de la page affichée
@app.callback(
    Output('refreshData', 'interval'),
    [Input('url', 'pathname')]
)
def update_interval(pathname):
    if pathname == "/live-map":
        return 30 * 1000 
    else:
        return 60 * 60 * 1000


################################################################################################
## CALLBACK PAGE LIVE MAP - FILTRES
################################################################################################
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

################################################################################################
## CALLBACK PAGE LIVE MAP - BOUTON FILTRE
#################################################################################################
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



################################################################################################
## CALLBACK PAGE STATS DATA - AFFICHAGE DATA DROPDOWN BLOC 1
################################################################################################

# Callback Gestion Affichage
# --------------------------
@app.callback(
    [
        Output('resultDropdown', 'children'),
        Output('titre-detail-complement', 'children'),
        Output('complement-dropdown', 'children')
    ],
    [
        Input('dropdown-airline', 'value'),
        Input('dropdown-dep-airport', 'value'),
        Input('dropdown-arr-airport', 'value'),
        Input('dropdown-aircraft', 'value')
    ]
)
def update_output(airline, dep_airport, arr_airport, aircraft):
    global global_statistics_df
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", "", ""
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]
        is_selected = bool(ctx.triggered[0]['value'])

        if is_selected:
            data_element = {}
            titre_complement = ''
            complement = ''

            if input_id == 'dropdown-airline':
                titre_complement = '  :  Compagnie Aérienne'
                data_element = get_data_one_element(airline, 'airline_iata', global_statistics_df)
            elif input_id == 'dropdown-dep-airport':
                titre_complement = '  :  Aéroport de départ'
                data_element = get_data_one_element(dep_airport, 'dep_iata', global_statistics_df)
            elif input_id == 'dropdown-arr-airport':
                titre_complement = '  :  Aéroport d\'arrivée'
                data_element = get_data_one_element(arr_airport, 'arr_iata', global_statistics_df)
            elif input_id == 'dropdown-aircraft':
                titre_complement = ':  Type d\'avion'
                data_element = get_data_one_element(aircraft, 'aircraft_icao', global_statistics_df)

            if titre_complement != '':
                complement = "( * Les données numériques sont des moyennes journalières sur la période disponible)"

            table_rows = []
            for key, value in data_element.items():
                table_rows.append(html.Tr([html.Td(key), html.Td(value)]))

            output_table = dbc.Table(
                [
                    html.Tbody(table_rows)
                ],
                bordered=False, striped=True, responsive=True
            )
            return output_table, titre_complement, complement

        else:
            return "", "", ""


# Callback Gestion "disabled" des dropdowns
# -----------------------------------------
@app.callback(
    [
        Output('dropdown-airline', 'disabled'),
        Output('dropdown-dep-airport', 'disabled'),
        Output('dropdown-arr-airport', 'disabled'),
        Output('dropdown-aircraft', 'disabled'),
    ],
    [
        Input('dropdown-airline', 'value'),
        Input('dropdown-dep-airport', 'value'),
        Input('dropdown-arr-airport', 'value'),
        Input('dropdown-aircraft', 'value'),
    ]
)
def disable_dropdowns(airline, dep_airport, arr_airport, aircraft):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, False, False, False
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]
        is_selected = bool(ctx.triggered[0]['value'])

        if is_selected:
            return [input_id != dropdown_id for dropdown_id in ['dropdown-airline', 'dropdown-dep-airport', 'dropdown-arr-airport', 'dropdown-aircraft']]
        else:
            return False, False, False, False


################################################################################################
## CALLBACK PAGE STATS DATA - GESTION DROPDOWN BLOC 2
################################################################################################

# callback dropdown airport_arrival
# ---------------------------------
@app.callback(
    Output("dropdown-callsign-arr", "options"),
    Output("dropdown-callsign-arr", "disabled"),
    Input("dropdown-callsign-dep", "value"),
)
def update_arrivee(depart):
    global global_statistics_df
    if depart is None or global_statistics_df is None:
        return [], True
    dic_airport_arr = get_dropdown_callsigns_aiprorts_arr(global_statistics_df, depart)
    arrivee_options = [{"label": name, "value": iata} for iata, name in dic_airport_arr.items()]
    return arrivee_options, False

# callback dropdown flight_numbers
# --------------------------------
@app.callback(
    Output("dropdown-callsign-num", "options"),
    Output("dropdown-callsign-num", "disabled"),
    Input("dropdown-callsign-dep", "value"),
    Input("dropdown-callsign-arr", "value"),
)
def update_flight_numbers(depart, arrivee):
    global global_statistics_df
    if depart is None or arrivee is None:
        return [], True
    flight_numbers = get_dropdowns_flight_numbers(global_statistics_df, depart, arrivee)
    return [{"label": i, "value": i} for i in flight_numbers], False

# callback affichage table résultats
# ----------------------------------
@app.callback(
    Output("result-callsign", "children"),
    Input("dropdown-callsign-dep", "value"),
    Input("dropdown-callsign-arr", "value"),
    Input("dropdown-callsign-num", "value"),
)
def create_table_callsign(depart, arrivee, callsign):
    global global_statistics_df
    if depart is None or arrivee is None or callsign is None:
        return ""
    df = get_table_callsign(global_statistics_df, depart, arrivee, callsign)
    flight_numbers = get_dropdowns_flight_numbers(global_statistics_df, depart, arrivee)
    return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

# Callback du DatePicker
@app.callback(
    Output('date_stat', 'data'),
    Input('date_picker', 'date'))
def update_date(date_value):
    return date_value
    

# Callback du dropdown aéroport de départ de la page Map stat
@app.callback(
    Output('dep_airport_data', 'data'),
    Input('dep_airport_stat', 'value'))
def update_dep_airport(airport):
    print(airport)
    return airport
    
# Callback du champ texte flight number de la page Map stat
@app.callback(
    Output('flight_number_data', 'data'),
    Input('flight_number_stat', 'value'))
def update_flight_number(flight_number):
    print(flight_number)
    return flight_number
    
# Callback du bouton 'ROUTES', qui permet d'afficher les routes d'un aéroport de départ, et d'un vol en particulier
@app.callback(
        Output("mapStat", "children"),
        [Input('routes_button', 'n_clicks'),
         State('date_stat', 'data'),
         State('dep_airport_data', 'data'),
         State('flight_number_data', 'data')
         ]
)
def routes_button(click, date, airport, flight_number):

    if click is None:
        raise PreventUpdate
    
    else:
        markers = create_markers()
        children = [dl.TileLayer(), *markers]

        if airport is not None:
            airports = get_datas(airport)
            polyline = create_patterns(airports)

            children = children + [*polyline]
        
        if flight_number is not None and flight_number:
            flight_positions = get_flight_positions(flight_number)
            flight_markers = create_flight_markers(flight_positions)

            children = children + [flight_markers]
    
    print("Mise à jour de la Map Stat réussie.")
    
    return children


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")

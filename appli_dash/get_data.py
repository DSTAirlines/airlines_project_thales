#!/usr/bin/python3
import os
import sys
from pathlib import Path
from pprint import pprint
import pandas as pd
import numpy as np
import re
from time import sleep
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import Airline, Aircraft, Airport, City, Country
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")
sys.path.append(f"{parent_dir}/live_api")

# Importer la fonction de connexion à MongoDB
from connection_mongodb import get_connection as connection_mongodb

# Importer la fonction de connexion à MySQL
from connection_sql import get_connection as connection_mysql

# Importer la fonction d'appel à l'API OpenSky
from fetch_opensky_data import query_opensky_api
from fetch_airlabs_data import query_airlabs_api

# Importer le module properties
import properties as pr

# CREDENTIALS
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
MONGO_COL_DATA_AGGREGATED = os.environ.get("MONGO_COL_DATA_AGGREGATED")



def get_data_initial():
    """
    S'effectue lors de l'ouverture de la page de la map Dash
    Récupère les données initiales depuis MongoDB pour la page de la map Dash
        -> les donnéees qui matchent entre data Airlabs et dernier enregistrement OpenSky
    Returns:
        Array: Liste de dict des données initiales
    """

    # Appel API OpenSky
    opensky_data = query_opensky_api()
    sleep(1)

    # Appel API Airlabs
    airlabs_data = query_airlabs_api()

    # convertir les deux listes en dictionnaires
    dict_opensky = {d['callsign']: d for d in opensky_data if d['callsign']!= '' and d['callsign'] is not None}
    dict_airlabs = {d['flight_icao']: d for d in airlabs_data if d['flight_icao']!= '' and d['flight_icao'] is not None}

    # créer une nouvelle liste pour stocker le résultat
    results = []

    # itérer sur chaque clé dans dict_opensky
    for key in dict_opensky:
        # si la clé est aussi dans dict_airlabs
        if key in dict_airlabs:
            dic = dict_opensky[key]
            dic['airlabs_doc'] = dict_airlabs[key]
            results.append(dic)
    return results


def get_data_dynamic_updated(old_data):
    """
    Quand refresh de la page map Dash, appel à l'API OpenSky
    On ne va garder que les old_data dont le callsign est présent dans le nouvel appel API
    Args:
        old_data (Array): Array des dict des data dynamiques actuellement affichés
    Returns:
        Array: Array d'update des data dynamiques des avions en vols
    """

    opensky_data = query_opensky_api()
    old_callsigns = [list(d.keys())[0] for d in old_data]
    return [data for data in opensky_data if data['callsign'] in old_callsigns]


# Extraire les données statiques SQL des éléments récupérés par API
def get_sql_data(df):
    """
    Récupère les données statiques SQL des éléments récupérés par API avec merge des infos
    Args:
        df (DataFrame): df de la fonction get_data_statistics
    Returns:
        DataFrame: df avec les données statiques SQL
    """
    list_dep_iata = df['dep_iata'].dropna().unique().tolist()
    list_arr_iata = df['arr_iata'].dropna().unique().tolist()
    list_airline_iata = df['airline_iata'].dropna().unique().tolist()
    list_aircraft_icao = df['aircraft_icao'].dropna().unique().tolist()

    lists_for_sql = {
        'aircrafts': list_aircraft_icao,
        'airlines': list_airline_iata,
        'view_airports': [list_dep_iata, list_arr_iata]
    }

    tables = ['aircrafts', 'airlines', 'view_airports']
    keys_sql = ['aircraft_icao', 'airline_iata', 'airport_iata']
    engine = connection_mysql()

    for i,table in enumerate(tables):
        list_mongo = lists_for_sql[table]
        sql = f'''
        SELECT * FROM {table};
        '''
        with engine.connect() as conn:
            query = conn.execute(text(sql))
        df_sql = pd.DataFrame(query.fetchall())

        if table != 'view_airports':
            key_sql = keys_sql[i]
            df_sql = df_sql[df_sql[key_sql].isin(list_mongo)]
            df_sql = df_sql.reset_index(drop=True)
            df_sql = df_sql.dropna(subset=[key_sql]).drop_duplicates(subset=[key_sql]).reset_index(drop=True)
            df = df.merge(df_sql, how='left', on=key_sql)
        
        else:
            for j,list_airport in enumerate(lists_for_sql['view_airports']):
                df_airport = df_sql.copy()
                airport = 'dep_iata' if j == 0 else 'arr_iata'
                key_sql = airport
                new_cols = []
                for col in list(df_airport.columns):
                    if col != 'airport_iata':
                        new_cols.append(f"{airport.split('_')[0]}_{col}")
                    else:
                        new_cols.append(airport)
                df_airport.columns = new_cols

                df_airport = df_airport[df_airport[key_sql].isin(list_airport)]
                df_airport = df_airport.reset_index(drop=True)
                df_airport = df_airport.dropna(subset=[key_sql]).drop_duplicates(subset=[key_sql]).reset_index(drop=True)
                df = df.merge(df_airport, how='left', on=airport)
    return df


def convert_time_unix_utc_to_datetime_fr(time_unix_utc):
    """ Convertir le temps unix UTC en datetime FR"""
    from datetime import datetime
    import pytz
    utc_datetime = datetime.utcfromtimestamp(time_unix_utc)
    paris_tz = pytz.timezone("Europe/Paris")
    local_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(paris_tz)
    datetime_fr = local_datetime.strftime('%Y-%m-%d %H:%M:%S')

    return datetime_fr


def validate_date(input_date):
    """ Valider la date entrée par l'utilisateur """

    # Vérifier le pattern
    if not re.match(r'\d{4}-\d{2}-\d{2}', input_date):
        return "date_incorrect_format"

    # Convertir la chaine de caractères en date
    try:
        input_date = datetime.strptime(input_date, '%Y-%m-%d')
    except ValueError:
        return "date_not_valid"

    # Vérifier si la date est dans la plage de temps
    today = datetime.today()
    a_week_ago = today - timedelta(days=7)

    if not a_week_ago <= input_date <= today:
        return "date_out_of_range"

    return "ok"


def get_data_statistics(date_data=None):
    """
    Récupère les données de la base MongoDB
    Arguments:
        date_data (str, optionnal): date de recherche (pour API - exemple 2023-10-01)
    Returns:
        DataFrame: Dataframe des données statistiques
    """
    
    print("STATS DATA - Création du DF_stats général")
    client = connection_mongodb()
    db = client[MONGO_DB_NAME]
    data = db['data_aggregated']

    cursor = data.find()
    df_temp = pd.DataFrame(list(cursor))

    client.close()

    if date_data is not None:
        df_temp['date_data'] = df_temp['datetime_start'].apply(lambda x: x.split(' ')[0])
        all_date_data = df_temp['date_data'].unique().tolist()
        if date_data not in all_date_data:
            return None
        cond1 = df_temp['count'] > 1
        cond2 = df_temp['date_data'] == date_data
        df_temp = df_temp[cond1 & cond2].reset_index(drop=True)

    else:
        min_time = df_temp['time_start'].min()
        max_time = df_temp['time_end'].max()
        df_temp = df_temp.drop('_id', axis=1)
        cond1 = df_temp['count'] > 1
        cond2 = df_temp['time_start'] > min_time
        cond3 = df_temp['time_end'] < max_time
        df_temp = df_temp[cond1 & cond2 & cond3].reset_index(drop=True)

    df = get_sql_data(df_temp)
    df['datetime_start'] = pd.to_datetime(df['datetime_start'])
    df['datetime_end'] = pd.to_datetime(df['datetime_end'])

    if date_data is None:
        last_day = df['datetime_start'].max().date()
        condition = df['datetime_start'].dt.date < last_day
        df = df[condition].reset_index(drop=True)

    df = df.astype({
        'dep_airport_latitude': 'float64',
        'dep_airport_longitude': 'float64',
        'arr_airport_latitude': 'float64',
        'arr_airport_longitude': 'float64',
    })
    return df


def get_global_stats(df):
    """
    Etablit les statistiques agrégées journalières
    Args:
        df (DataFrame): Le dataframe de la fonction get_sql_data
    Returns:
        DataFrame: Dataframe des données agrégées
    """
    stats_global = df.groupby(pd.Grouper(key='datetime_start', freq='D')).agg({
        'callsign': 'nunique',
        'airline_iata': 'nunique',
        'dep_iata': 'nunique',
        'arr_iata': 'nunique',
    })
    return stats_global



def get_drop_dic_individual_stats(value_col, label_col, df):
    """
    Produit les listes pour les dropdowns des statistiques
    Args:
        value_col (str): Value recherchée (code iata généralement)
        label_col (str): Nom de la colonne du dataframe correspondant
        df (DataFrame): Df des données globales
    Returns:
        dict: dict pour affichage des dropdowns
    """
    df_temp = df[[value_col, label_col]].dropna()
    df_temp = df_temp.reset_index()
    df_temp = df_temp.sort_values(by=label_col)
    dic = df_temp.set_index(value_col)[label_col].to_dict()
    return dic


def get_data_one_element(value_col, label_col, df):
    """
    Récupère les données statistique d'un élément (un aéroport, une compagnie aérienne, un avion)
    puis effectue une agrégation journalière des données
    pour affichage dans une table
    Args:
        value_col (str): Value recherchée (code iata généralement)
        label_col (str): Nom de la colonne du dataframe correspondant
        df (DataFrame): Df des données globales
    Returns:
        dict: dict pour affichage des résultats dans une table
    """
    dic_return = {}
    df = df[df[label_col] == value_col]
    df = df.reset_index(drop=True)
    if label_col == 'airline_iata':
        cols = ['callsign', 'datetime_start', 'airline_iata', 'airline_icao', 'airline_name', 
        'arr_iata', 'dep_iata', 'aircraft_icao']
        df = df[cols]
        ddf =  df.groupby(pd.Grouper(key='datetime_start', freq='D')).agg({
            'callsign': 'nunique',
            'arr_iata': 'nunique',
            'dep_iata': 'nunique',
            'aircraft_icao': 'nunique',
        })
        len_df = len(ddf)
        dic_return = {
            'Nom': df.loc[0, 'airline_name'],
            'Code IATA': value_col,
            'Code ICAO': df.loc[0, 'airline_icao'],
            'Nb de vols': f"{round(ddf['callsign'].sum() / len_df)} / j",
            'Nb d\'aéroprts de départ': f"{round(ddf['dep_iata'].sum() / len_df)} / j",
            'Nb d\'aéroprts d\'arrivée': f"{round(ddf['arr_iata'].sum() / len_df)} / j",
            'Nb de types d\'avions': f"{round(ddf['aircraft_icao'].sum() / len_df)} / j",
        }

    elif label_col == 'aircraft_icao':
        cols = ['callsign', 'datetime_start', 'airline_iata', 'arr_iata', 'dep_iata', 
        'aircraft_flag', 'aircraft_reg_number', 'aircraft_iata', 'aircraft_name', 
        'aircraft_wiki_link']
        df = df[cols]
        ddf =  df.groupby(pd.Grouper(key='datetime_start', freq='D')).agg({
            'callsign': 'nunique',
            'arr_iata': 'nunique',
            'dep_iata': 'nunique',
            'airline_iata': 'nunique',
        })
        len_df = len(ddf)
        dic_return = {
            'Nom': df.loc[0, 'aircraft_name'],
            'Code IATA': df.loc[0, 'aircraft_iata'],
            'Code ICAO': value_col,
            'Nb de vols': f"{round(ddf['callsign'].sum() / len_df)} / j",
            'Nb d\'aéroprts de départ': f"{round(ddf['dep_iata'].sum() / len_df)} / j",
            'Nb d\'aéroprts d\'arrivée': f"{round(ddf['arr_iata'].sum() / len_df)} / j",
            'Nb de comapgnies': f"{round(ddf['airline_iata'].sum() / len_df)} / j",
        }

    elif label_col in ['dep_iata', 'arr_iata']:
        pre_ = f"{label_col.split('_')[0]}_"
        cols_without_pre = ['airport_icao', 'airport_name', 'airport_utc_offset_str',
            'airport_wiki_link', 'country_name', 'city_name', 'country_iso2']
        cols = ['callsign', 'datetime_start', 'airline_iata', 'aircraft_icao']
        cols.extend([pre_ + c for c in cols_without_pre])
        cols.append("dep_iata" if label_col == 'arr_iata' else "arr_iata")
        df = df[cols]
        other = 'arr_iata' if label_col == 'dep_iata' else 'dep_iata'
        ddf =  df.groupby(pd.Grouper(key='datetime_start', freq='D')).agg({
            'callsign': 'nunique',
            other: 'nunique',
            'airline_iata': 'nunique',
            'aircraft_icao': 'nunique',
        })
        len_df = len(ddf)
        other_str = 'Nb d\'aéroports de destination' if label_col == 'dep_iata' else 'd\'origine'
        dic_return = {
            'Nom': df.loc[0, f"{pre_}airport_name"],
            'Localisation': df.loc[0, f"{pre_}city_name"] + " - " + 
                df.loc[0, f"{pre_}country_name"].upper() + 
                " (" + df.loc[0, f"{pre_}country_iso2"] + ")",
            'Codes IATA / ICAO': f"{value_col}" + " / " + df.loc[0, f"{pre_}airport_icao"],
            'UTC offset': df.loc[0, f'{pre_}airport_utc_offset_str'],
            'Nb de vols': f"{round(ddf['callsign'].sum() / len_df)} / j",
            'Nb de compagnies': f"{round(ddf['airline_iata'].sum() / len_df)} / j",
            other_str: f"{round(ddf[other].sum() / len_df)} / j",
            'Nb de types d\'avions': f"{round(ddf['aircraft_icao'].sum() / len_df)} / j",
        }
    return dic_return


def get_dropdown_callsigns_aiprorts_dep(df):
    """
    Obtenir les airports de départ possibles, cad ceux présents dans les données globales de stats
    Args:
        df (DataFrame): DF des données globales de stats
    Returns:
        dict: Options du dropdown "airport de départ"
    """
    df = df.drop_duplicates(subset=['callsign']).reset_index(drop=True)
    df = df[['callsign', 'dep_iata', 'dep_icao', 'dep_airport_name']].dropna().drop_duplicates().reset_index(drop=True)

    df = df.sort_values(by=['dep_airport_name'])
    df['new_name'] = df['dep_airport_name'] + ' (' + df['dep_iata'] + ' / ' + df['dep_icao'] + ')'
    dic = df.set_index('dep_iata')['new_name'].to_dict()

    return dic

def get_dropdown_callsigns_aiprorts_arr(df, dep_iata):
    """
    Obtenir les airports d'arrivée correspondant à l'airport d'origine sélectionné
    Args:
        df (DataFrame): DF des données globales de stats
        dep_iata (str): code IATA de l'airports d'origine
    Returns:
        dict: Options du dropdown "airport d'arrivée"
    """
    df = df.drop_duplicates(subset=['callsign']).reset_index(drop=True)
    df = df[['callsign', 'dep_iata', 'dep_airport_name', 'arr_iata', 'arr_icao', 'arr_airport_name']].dropna().drop_duplicates().reset_index(drop=True)
    df = df[df['dep_iata'] == dep_iata].drop_duplicates(subset=['arr_iata']).reset_index(drop=True)
    df = df.sort_values(by=['arr_airport_name'])

    df['new_name'] = df['arr_airport_name'] + ' (' + df['arr_iata'] + ' / ' + df['arr_icao'] + ')'
    dic = df.set_index('arr_iata')['new_name'].to_dict()
    return dic


def get_dropdowns_flight_numbers(df, dep_iata, arr_iata):
    """
    Obtenir les callsigns correspondant aux airports d'origine et d'arrivée slectionnés
    Args:
        df (DataFrame): DF des données globales de stats
        dep_iata (str): code IATA de l'airports d'origine
        arr_iata (str): code IATA de l'airports d'arrivée
    Returns:
        dict: Options du dropdown "callsign"
    """
    df = df.drop_duplicates(subset=['callsign']).reset_index(drop=True)
    df = df[['callsign', 'dep_iata', 'arr_iata']].drop_duplicates().dropna().reset_index(drop=True)
    cond1 = (df['dep_iata'] == dep_iata)
    cond2 = (df['arr_iata'] == arr_iata)
    df = df[cond1 & cond2].reset_index(drop=True)
    if len(df) != 0:
        return sorted(list(set(df['callsign'].tolist())))
    else:
        return []


def get_table_callsign(df, dep_iata, arr_iata, callsign):
    """
    Obtenir le df des données correspondant aux dropdowns sélectionnés
    Args:
        df (DataFrame): DF des données globales de stats
        dep_iata (str): code IATA de l'airports d'origine
        arr_iata (str): code IATA de l'airports d'arrivée
        callsign (str): code du callsign
    Returns:
        DataFrame: DF des données filtrées
    """
    df = df.drop_duplicates().dropna().reset_index(drop=True)
    cond1 = (df['dep_iata'] == dep_iata)
    cond2 = (df['arr_iata'] == arr_iata)
    cond3 = (df['callsign'] == callsign)
    df = df[cond1 & cond2 & cond3]
    df = df.sort_values(by=['datetime_start'], ascending=True).reset_index(drop=True)

    if len(df) > 1:
        i_to_del = []
        for i in range(len(df) - 1):
            time_dep1 = df.loc[i, 'datetime_start']
            time_arr1 = df.loc[i, 'datetime_end']
            time_dep2 = df.loc[i+1, 'datetime_start']
            time_arr2 = df.loc[i+1, 'datetime_end']
            if (time_dep2 - time_arr1).seconds < 1500:
                i_to_del.append(i)
                df.loc[i+1, 'datetime_start'] = df.loc[i, 'datetime_start']
        if len(i_to_del) > 0:
            df = df.drop(index=i_to_del).reset_index(drop=True)

    cols = [
        'callsign', 'datetime_start', 'datetime_end', 
        'airline_iata', 'airline_icao', 'airline_name',
        'aircraft_name', 'aircraft_iata', 'aircraft_icao',
        'dep_city_name', 'dep_country_name',
        'arr_city_name', 'arr_country_name',
    ]

    df = df[cols]
    df['travel_time'] = df['datetime_end'] - df['datetime_start']
    df['travel_time'] = df['travel_time'].apply(lambda x: f"{x.seconds // 3600}h {x.seconds // 60 % 60}m")
    df['datetime_start'] = df['datetime_start'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    df['datetime_end'] = df['datetime_end'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    df['airline'] = df['airline_name'] + ' (' + df['airline_iata'] + ' / ' + df['airline_icao'] + ')'
    df['dep_country_name'] = df['dep_country_name'].apply(lambda x: x.upper())
    df['arr_country_name'] = df['arr_country_name'].apply(lambda x: x.upper())
    df['dep'] = df['dep_city_name'] + ' - ' + df['dep_country_name']
    df['arr'] = df['arr_city_name'] +' - '+ df['arr_country_name']
    df['appareil'] = df['aircraft_name'] + ' (' + df['aircraft_iata'] + ' / ' + df['aircraft_icao'] + ')'

    df = df[['callsign', 'datetime_start', 'datetime_end', 'travel_time', 'airline', 'dep', 'arr', 'appareil']]
    df = df.sort_values(by=['datetime_start'])
    df.columns = ['N° de vol', 'Départ', 'Arrivée', 'Temps de Trajet', 'Compagnie', 'Ville Depart', 'Ville Arrivée', 'Appareil']
    if len(df) == 0:
        for col in df.columns:
            df.loc[0, col] = "-" if col != 'N° de vol' else callsign
    return df

# Liste de tous les aéroports en base de données SQL pour dropdown de la Map stat
def get_airports():
    """
    Retourne la liste de tous les aéroports de la Map Stat (en Europe), pour le dropdown 'Aéroport de départ'
    """
    
    AIRPORT_NAME_INDEX = 0
    AIRPORT_IATA_INDEX = 1

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
    
    airports = [{'label': airport[AIRPORT_NAME_INDEX], 'value': airport[AIRPORT_IATA_INDEX]} for airport in airports]
    
    return airports

# Liste de tous les aéroports à afficher sur la MAP STAT
def get_datas(dep_airport):
    """
    Retourne la liste de toutes les coordonnées des aéroports les plus désservis à partir de l'aéroport de départ (dep_airport) de la Map Stat
    """

    AIRPORT_IATA_INDEX = 0
    AIRPORT_LATITUDE_INDEX = 1
    AIRPORT_LONGITUDE_INDEX = 2

    client = connection_mongodb()
    db = client[MONGO_DB_NAME]
    datas_collection = db[MONGO_COL_DATA_AGGREGATED]

    pipeline = [
        {
            "$match": {
                "dep_iata": dep_airport,
                "arr_iata": {"$nin": [dep_airport, None]},
            }
        },
        {
            "$group": {
                "_id": "$callsign",
                "arr_airport": {"$addToSet": "$arr_iata"},
            }
        },
        {
            "$unwind": {
                "path": "$arr_airport",
                "preserveNullAndEmptyArrays": True,
            }
        },
        {
            "$group": {
                "_id": "$arr_airport",
                'count': { '$count': {} }
            }
        },
        {
            "$sort": {"count": -1},
        },
        {
            "$limit": 15,
        },
    ]

    airports_without_coordinates = list(datas_collection.aggregate(pipeline))
    airports_with_coordinates = []
    engine = connection_mysql()

    for airport in airports_without_coordinates:
        sql_request = f"""
            SELECT airport_iata, airport_latitude, airport_longitude FROM airports 
            WHERE airport_iata = '{airport['_id']}';
        """

        with engine.connect() as conn:

            query = conn.execute(text(sql_request))
            airport = query.all()
            airports_with_coordinates.append({'airport_iata': airport[0][AIRPORT_IATA_INDEX], 'airport_latitude': airport[0][AIRPORT_LATITUDE_INDEX],
                     'airport_longitude': airport[0][AIRPORT_LONGITUDE_INDEX]})

    sql_request_dep_airport = f"""
            SELECT airport_iata, airport_latitude, airport_longitude FROM airports 
            WHERE airport_iata = '{dep_airport}';
    """

    with engine.connect() as conn:
        query = conn.execute(text(sql_request_dep_airport))
        dep_airport = query.first()

    dep_airport = dict(airport_iata=dep_airport[0], airport_latitude=dep_airport[1], airport_longitude=dep_airport[2])
    airports_with_coordinates.insert(0, dep_airport)

    client.close()

    return airports_with_coordinates

# Retourne toutes les positions (latitude et longitude) du vol pendant la journée en cours
def get_flight_positions(flight_number, api=False):
    """
    Retourne les positions du vol donné par le numéro de vol en entré
    """

    day_date = datetime.now().strftime("%Y-%m-%d")
    day_date_after = (datetime.now() + timedelta(days= 1)).strftime('%Y-%m-%d')

    client = connection_mongodb()
    db = client[MONGO_DB_NAME]
    datas_collection = db[MONGO_COL_OPENSKY]

    airplane_datas = datas_collection.find({'callsign': flight_number, 'datatime': {'$gte': day_date, '$lte': day_date_after}}).sort("datatime", 1)
    
    if api:
        cleaned_airplane_datas = []
        for airplane in airplane_datas:

            client = connection_mongodb()
            db = client[MONGO_DB_NAME]
            airlabs_col = db[MONGO_COL_AIRLABS]

            if airplane['airlabs_id'] is not None:
                airlabs_data = airlabs_col.find_one({'_id': airplane['airlabs_id']}, {'_id': 0, 'flag': 1, 'arr_iata': 1, 'flight_iata': 1, 
                                                                                      'dep_iata': 1, 'airline_iata': 1})
                airplane.update(airlabs_data)

            airplane.pop('_id')
            airplane.pop('airlabs_id')
            airplane.pop('time_position')
            airplane.pop('time')
            airplane.pop('last_contact')
            airplane.pop('icao_24')
            
            cleaned_airplane_datas.append(airplane)

        return list(cleaned_airplane_datas)
    
    airplane_positions = [{'latitude': airplane ['latitude'], 'longitude': airplane['longitude']} for airplane in airplane_datas]

    client.close()

    return airplane_positions


##########################################################
# Fonctions API
##########################################################


def get_static_data_api(table, elements=[]):
    """
    Retourne les enregistrements de la base de données MySQL
    Args:
        table (str): Nom de la table
        element (array, optionnal): Code de l'élément à récupérer (Primary Key de la table)
    Returns:
        Array: Array des dictionnaires des enregistrements de la table
    """

    # Dictionnaire de correspondance table - primary key
    dic_primary_keys = {
        "airports": "airport_iata",
        "airlines": "airline_iata",
        "aircrafts": "aircraft_iata",
        "countries": "country_iso2",
        "cities": "city_iata",
    }

    # Récupération de la connexion à la base de données
    engine = connection_mysql()

    sql = f'''
    SELECT * FROM {table}
    '''
    if len(elements) > 0:
        pk = dic_primary_keys[table]
        placeholders = ', '.join(['%s'] * len(elements))
        sql += f'''
        WHERE {pk} IN ({placeholders})
        '''
    with engine.connect() as conn:
        query = conn.execute(str(sql), elements)

    return [dict(row) for row in query.fetchall()]

def get_data_statistics_type_data_api(df, type_data, elements):
    """
    Retourne les enregistrements de la collection des données agrégées MongoDB filtrés par les paramètres spécifiées
    Args:
        df_stats (DataFrame): DataFrame des données agrégées
        type_data (str): Type de données à récupérer
        elements (array): Valeur(s) de la variable "type_data" à récupérer
    Returns:
        Dict: Dictionnaires des données agrégées filtrés par les paramètres spécifiées
    """
    if df is not None and type_data is not None:
        if type_data == 'city_iata':
            list_values = df['dep_fk_city_iata'].unique().tolist()
            list_values.extend(df['arr_fk_city_iata'].unique().tolist())
        elif type_data == 'country_iso2':
            list_values = df['dep_country_iso2'].unique().tolist()
            list_values.extend(df['arr_country_iso2'].unique().tolist())
        else:
            list_values = df[type_data].unique().tolist()
        list_values_ok = list(set(elements).intersection(list_values))

        if len(list_values_ok) > 0:
            if type_data == 'city_iata':
                df = df[(df['dep_fk_city_iata'].isin(elements)) | (df['arr_fk_city_iata'].isin(elements))].drop(['airline_number', 'dep_airport_icao', 'arr_airport_icao'], axis=1).reset_index(drop=True)
            elif type_data == 'country_iso2':
                df = df[(df['dep_country_iso2'].isin(elements)) | (df['arr_country_iso2'].isin(elements))].drop(['airline_number', 'dep_airport_icao', 'arr_airport_icao'], axis=1).reset_index(drop=True)
            else:
                df = df[df[type_data].isin(elements)].drop(['airline_number', 'dep_airport_icao', 'arr_airport_icao'], axis=1).reset_index(drop=True)
            df['datetime_start'] = df['datetime_start'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            df['datetime_end'] = df['datetime_end'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            df = df.replace(np.nan, None)
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            df = df.sort_values(['datetime_start', 'datetime_end'])
            if len(df)>0:
                return df.to_dict('records')
    return None


def admin_api(table, action, data=None, pk_value=None):
    """
    Fonction d'administration des données
    Args:
        table (str): Nom de la table
        action (str): Action à effectuer
        data (dict): Dictionnaire des données
    Returns:
        None
    """

    dic_tables_requirements = {
        'airlines':{
            'pk': 'airline_iata',
            'fk': None,
            'requirements_fields': {
                'airline_iata':
                    { 'type': 'string',  'length': 2,    'required': True  },
                'airline_icao':
                    { 'type':'string',   'length': 3,    'required': False },
                'airline_name':
                    { 'type':'string',   'length': None, 'required': False }
            }
        },
        'aircrafts':{
            'pk': 'aircraft_iata',
            'fk': None,
            'requirements_fields': {
                'aircraft_iata' :
                    { 'type':'string',   'length': 3,      'required': True  },
                'aircraft_icao':
                    { 'type':'string',   'length': 4,      'required': False },
                'aircraft_name':
                    { 'type':'string',   'length': None,   'required': False },
                'aircraft_wiki_link':
                    { 'type':'string',   'length': None,   'required': False }
            }
        },
        'airports':{
            'pk': 'airport_iata',
            'fk': {
                'field': 'fk_city_iata',
                'referenced_table': 'cities',
                'referenced_field': 'city_iata'
            },
           'requirements_fields': {
                'airport_iata':
                    { 'type':'string',  'length': 3,    'required': True  },
                'airport_icao':
                    { 'type':'string',  'length': 4,    'required': False },
                'fk_city_iata':
                    { 'type':'string',  'length': 3,    'required': True  },
                'airport_name':
                    { 'type':'string',  'length': None, 'required': False },
                'airport_utc_offset_str':
                    { 'type':'string',  'length': None, 'required': False },
                'airport_utc_offset_min':
                    { 'type':'integer', 'length': None, 'required': False },
                'airport_timezone_id':
                    { 'type':'string',  'length': None, 'required': False },
                'airport_latitude':
                    { 'type':'float',   'length': None, 'required': False },
                'airport_longitude':
                    { 'type':'float',   'length': None, 'required': False },
                'airport_wiki_link':
                    { 'type':'string',  'length': None, 'required': False }
           }
        }
    }

    dic_table = dic_tables_requirements[table]
    pk = dic_table['pk']
    fk = dic_table['fk']
    dict_values = {}

    if data is not None:
        for k, v in data.items():
            if 'iata' in k or 'icao' in k:
                dict_values[k] = v.upper() if v is not None else None
            if k in list(dic_table['requirements_fields'].keys()):
                requirements = dic_table['requirements_fields'][k]

                if action == 'post':
                    if requirements['required'] is not False:
                        if v is None:
                            return {'error': f'Le champ {k} est un champ obligatoire'}

                if v is not None:
                    if requirements['type'] == 'string':
                        if isinstance(v, str) is False:
                            try:
                                v = str(v)
                            except:
                                return {'error': 'Type de données invalide'}
                    elif requirements['type'] == 'integer':
                        if isinstance(v, int) is False:
                            try:
                                v = int(v)
                            except:
                                return {'error': 'Type de données invalide'}
                    elif requirements['type'] == 'float':
                        if isinstance(v, float) is False:
                            try:
                                v = float(v)
                            except:
                                return {'error': 'Type de données invalide'}

                    if requirements['length'] is not None:
                        if len(str(v)) != requirements['length']:
                            return {'error': f'La longueur du champ {k} n\'est pas conforme à la longueur autorisée'}

                    dict_values[k] = v

            else:
                return {'error': f'Le champ {k} n\'est pas présent dans la table {table}'}

    if action == 'post':
        # Vérification que la valeur du champ 'pk' n'est pas déjà présent dans la table
        if check_primary_key(table, pk, data[pk]) is False:
            return {'error': f'La valeur {data[pk]} existe déjà comme clé primaire {pk} de la table {table}'}

    # Récupération de la connexion à la base de données
    engine = connection_mysql()
    # Créer une session
    session = Session(engine)

    # Créer une instance de la classe SQLAlchemy de la table avec le dictionnaire dict_values
    if table == 'airlines':
        if action == 'post':
            new_instance = Airline(**dict_values)
        elif action == 'put' or action == 'delete':
            new_instance = session.query(Airline).filter_by(airline_iata=pk_value).first()
    elif table == 'aircrafts':
        if action == 'post':
            new_instance = Aircraft(**dict_values)
        elif action == 'put' or action == 'delete':
            new_instance = session.query(Aircraft).filter_by(aircraft_iata=pk_value).first()
    elif table == 'airports':
        if action == 'post':
            new_instance = Airport(**dict_values)
        elif action == 'put' or action == 'delete':
            new_instance = session.query(Airport).filter_by(airport_iata=pk_value).first()
    else:
        return {'error': f'La table {table} n\'existe pas'}

    # Ajout et commit de la modif de la base de données
    if action == 'post':
        session.add(new_instance)
    elif action == 'put':
        for field, value in dict_values.items():
            setattr(new_instance, field, value)
    elif action == 'delete':
        session.delete(new_instance)
    else:
        return {'error': f'L\'action {action} n\'existe pas'}
    session.commit()

    # Fermer la session
    session.close()

    return {'success': True}


def check_primary_key(table, pk_field, pk_value):
    """
    Vérifier l'bscence d'une valeur comme clé primaire pour une table SQL
    Args:
        table (str): Nom de la table
        pk_field (str): Nom de la clé primaire
        pk_value (str): Valeur de la clé primaire à vérifier
    Returns:
        bool: True si valeur n'existe pas comme clé primaire, False sinon
    """
    engine = connection_mysql()

    query_pk = f'''
    SELECT * FROM {table} WHERE {pk_field} = '{pk_value}'
    '''
    with engine.connect() as conn:
        query = conn.execute(str(query_pk))

    if query.rowcount != 0:
        return False

def get_value_pk_airports(pk_value):
    """
    Obtenir la valeur de la clé étrangère pour une valeur de clé primaire donnée pour la table airports
    Args:
        pk_value (str): Valeur de la clé primaire
    Retirns:
        str: Valeur de la clé étrangère
    """
    engine = connection_mysql()

    query_pk = f'''
    SELECT fk_city_iata FROM airports WHERE airport_iata = '{pk_value}'
    '''
    with engine.connect() as conn:
        query = conn.execute(str(query_pk))

    if query.rowcount!= 0:  
        return query.fetchone()[0]
    return None


##########################################################
# Fonctions API - Données dynamiques
##########################################################

def get_flights_api(callsign=None, dep_airport=None, arr_airport=None, airline_company=None, origin_country=None):

    client = connection_mongodb()
    db = client[MONGO_DB_NAME]
    opensky_col = db[MONGO_COL_OPENSKY]
    airlabs_col = db[MONGO_COL_AIRLABS]

    flights_aggr = []

    last_time = opensky_col.find().sort("datatime", -1)[0]['datatime']
    flights_dyn = opensky_col.find({"datatime": last_time})
    
    for flight in flights_dyn:
        if flight['airlabs_id'] is not None:
            flight_stat = airlabs_col.find({'_id': flight['airlabs_id']})[0]
            flight_dict = {
                'flight_number': flight_stat['flight_number'],
                'depart_airport': flight_stat['dep_iata'],
                'arrival_airport': flight_stat['arr_iata'],
                'airline_company': flight_stat['airline_iata'],
                'origin_country_code': flight_stat['flag']
            }
            flight.update(flight_dict)
        
        flight.pop('_id')
        flight.pop('airlabs_id')
        flight.pop('icao_24')
        flight.pop('time')
        flight.pop('last_contact')
        flight.pop('time_position')

        flights_aggr.append(flight)

    client.close()

    test_flight_by_filter = lambda flight_value, filter_value: flight_value == filter_value if filter_value is not None else flight_value
    
    if callsign or dep_airport or arr_airport or airline_company or origin_country:
        filtered_flights = [flight for flight in flights_aggr if
            (test_flight_by_filter(flight.get('depart_airport'), dep_airport))
            and
            (test_flight_by_filter(flight.get('arrival_airport'), arr_airport))
            and
            (test_flight_by_filter(flight.get('airline_company'), airline_company))
            and
            (test_flight_by_filter(flight.get('origin_country'), origin_country))
            and
            (test_flight_by_filter(flight.get('callsign'), callsign))]
        
        if not filtered_flights:
            return '404'
        
        return filtered_flights
        
    return flights_aggr
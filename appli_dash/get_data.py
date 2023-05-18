#!/usr/bin/python3
import os
import sys
from pathlib import Path
from pprint import pprint
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
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

    # Connexion à MongoDB
    client = connection_mongodb()
    db = client[MONGO_DB_NAME]
    opensky_collection = db[MONGO_COL_OPENSKY]

    # Recherche du "time" le plus récent
    max_time_result = opensky_collection.find().sort("time", -1).limit(1)
    max_time = max_time_result[0]["time"]

    # Recherche des documents du dernier enregistrement avec un airlabs_id non nul
    pipeline = [
        {"$match": {"time": max_time, "airlabs_id": {"$ne": None}}},
        {"$lookup": {
            "from": "airlabs",
            "localField": "airlabs_id",
            "foreignField": "_id",
            "as": "airlabs_doc"
        }},
        {"$unwind": "$airlabs_doc"},
    ]

    results = list(opensky_collection.aggregate(pipeline))
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



# def get_dic_countries():
#     """
#     Récupère correspondances pour les pays du code iso2 et du nom
#     Args:
#         None
#     Returns:
#         dict: dict de la forme dic['iso2'] = 'country_name'
#     """
#     engine = connection_mysql()
#     sql = f'''
#     SELECT country_iso2, country_name FROM countries;
#     '''
#     with engine.connect() as conn:
#         query = conn.execute(text(sql))
#     df_countries = pd.DataFrame(query.fetchall())
#     dic_countries = df_countries.set_index('country_iso2')['country_name'].to_dict()
#     return dic_countries


# Extraire les données statiques SQL des éléments récupérés par API
def get_sql_data(df):
    """
    Récupère les données statiques SQL des éléments récupérés par API avec merge des infos
    Args:
        df (DataFrame): df de la fonction get_data_statistics
    Returns:
        _type_: _description_
    """
    list_dep_iata = df['dep_iata'].dropna().unique().tolist()
    list_arr_iata = df['arr_iata'].dropna().unique().tolist()
    # list_arr = list(set(list_arr_iata) | set(list_dep_iata))
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
    from datetime import datetime
    import pytz
    utc_datetime = datetime.utcfromtimestamp(time_unix_utc)
    paris_tz = pytz.timezone("Europe/Paris")
    local_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(paris_tz)
    datetime_fr = local_datetime.strftime('%Y-%m-%d %H:%M:%S')

    return datetime_fr

def get_data_statistics():
    """
    Récupère les données de la base MongoDB
    Returns:
        DataFrame: Dataframe des données statistiques
    """
    print("STATS DATA - STEP 1 : Création du DF_stats général")
    client = connection_mongodb()
    db = client[MONGO_DB_NAME]
    data = db['data_aggregated']

    cursor = data.find()
    df_temp = pd.DataFrame(list(cursor))

    # Fermer la connexion
    client.close()

    print(f"STATS DATA - STEP 1 : len df_temp brut : {len(df_temp)}")

    min_time = df_temp['time_start'].min()
    max_time = df_temp['time_end'].max()
    
    df_temp = df_temp.drop('_id', axis=1)
    cond1 = df_temp['count'] > 1
    cond2 = df_temp['time_start'] > min_time
    cond3 = df_temp['time_end'] < max_time
   
    df_temp = df_temp[cond1 & cond2 & cond3].reset_index(drop=True)

    print(f"STATS DATA - STEP 1 : len df_temp {len(df_temp)}")

    df = get_sql_data(df_temp)
    df['datetime_start'] = pd.to_datetime(df['datetime_start'])
    df['datetime_end'] = pd.to_datetime(df['datetime_end'])
    last_day = df['datetime_start'].max().date()
    condition = df['datetime_start'].dt.date < last_day
    df = df[condition].reset_index(drop=True)
    df = df.astype({
        'dep_airport_latitude': 'float64',
        'dep_airport_longitude': 'float64',
        'arr_airport_latitude': 'float64',
        'arr_airport_longitude': 'float64',
    })
    print(f"STATS DATA - STEP 1 : len de df général : {len(df)}")
    # df.to_csv('test.csv', header=True, index=False)
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
    print(stats_global)
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
    """_summary_

    Args:
        value_col (str): Value recherchée (code iata généralement)
        label_col (str): Nom de la colonne du dataframe correspondant
        df (DataFrame): Df des données globales
        dic_countries (dict, optional): Pour les aircrafts seulement (Defaults to None)
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
        # flag = df.loc[0, 'aircraft_flag']
        # if dic_countries is not None:
        #     flag = dic_countries.get(flag, flag)
        dic_return = {
            'Nom': df.loc[0, 'aircraft_name'],
            'Code IATA': df.loc[0, 'aircraft_iata'],
            'Code ICAO': value_col,
            # 'N° d\'enregistrement': df.loc[0, 'aircraft_reg_number'],
            # 'Pays d\'enregistrement': flag,
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
    Obtenir les airports d'arrivée correspondant à l'airports d'origine sélectionné
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
    return sorted(list(set(df['callsign'].tolist())))


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
    
    cols = [
        'datetime_start', 'datetime_end', 
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

    df = df[['datetime_start', 'datetime_end', 'travel_time', 'airline', 'dep', 'arr', 'appareil']]
    df = df.sort_values(by=['datetime_start'])
    df.columns = ['Départ', 'Arrivée', 'Temps de Trajet', 'Compagnie', 'Ville Depart', 'Ville Arrivée', 'Appareil']
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
            "$match": 
            {
                "dep_iata": dep_airport,
                "arr_iata": {"$nin": [dep_airport, None]},
                
            }
        },
        {
            "$group":
            {
                '_id':'$callsign',
                'arr_airport': 
                {
                    '$addToSet':'$arr_iata'
                }
            }
        },
        {
            "$unwind":
            {
                'path': "$arr_airport",
                'preserveNullAndEmptyArrays': True
            }

        },
        {
            "$group":
            {
                '_id':'$arr_airport',
                'count': {
                    '$count': {}
                }
            }
        },

        {
            "$sort": 
            {
                'count': -1
            }
        },
        {
            '$limit':15
        }
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
def get_flight_positions(flight_number):
    """
    Retourne les positions du vol donné par le numéro de vol en entré
    """

    day_date = datetime.now().strftime("%Y-%m-%d")
    day_date_after = (datetime.now() + timedelta(days= 1)).strftime('%Y-%m-%d')

    client = connection_mongodb()
    db = client[MONGO_DB_NAME]
    datas_collection = db[MONGO_COL_OPENSKY]

    airplane_datas = datas_collection.find({'callsign': flight_number, 'datatime': {'$gte': day_date, '$lte': day_date_after}}).sort("datatime", 1)

    airplane_positions = [{'latitude': airplane ['latitude'], 'longitude': airplane['longitude']} for airplane in airplane_datas]

    client.close()

    return airplane_positions
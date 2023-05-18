from flask import Blueprint, jsonify, request, make_response
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
from pydantic import BaseModel, ValidationError, validator
from flask_pydantic import validate
from get_data import *
from typing import Optional


# ----------------------------------------------
# Définition du blueprint API
# ----------------------------------------------
api = Blueprint('api', __name__)


# ----------------------------------------------
# Gestion automatisée des erreurs
# ----------------------------------------------

# Gestion d'une demande mal formée (400)
@api.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify(error=str(e)), 400

# Gestion d'une ressource non trouvée (404)
@api.errorhandler(NotFound)
def handle_not_found(e):
    return jsonify(error=str(e)), 404

# Gestion d'une erreur interne du serveur (500)
@api.errorhandler(InternalServerError)
def handle_internal_error(e):
    return jsonify(error="Une erreur interne est survenue. Veuillez réessayer plus tard."), 500


# ----------------------------------------------
# Dictionnaires de conversion
# ----------------------------------------------

dic_var_stats = {
    'callsign': 'callsign',
    'departure_airport': 'dep_iata',
    'arrival_airport': 'arr_iata',
    'airline': 'airline_iata',
    'aircraft': 'aircraft_icao',
    'country': 'country_iso2',
    'city': 'city_iata'
}



# ----------------------------------------------
# Définition des classes enfants de BaseModel
# ----------------------------------------------

class DataStatic(BaseModel):
    """Class permettant de récupérer les données statiques"""
    category: str
    elements_static: Optional[str] = None

class DataStatistic(BaseModel):
    """Class permettant de récupérer les données agrégées"""
    type_data: str
    elements_statistic: str
    date_data: Optional[str] = None


# ----------------------------------------------
# Définition des routes
# ----------------------------------------------

# ROUTE STATIC_DATA
@api.route('/static_data', methods=['GET'])
@validate()
def static_data(query: DataStatic):
    """
    Retourne les données statiques de la base de données
    ---
    tags:
        - static_data
    parameters:
        - name: category
          in: query
          description: |
            Nom de la catégorie (`airports`, `airlines`, `aircrafts`, `countries`, `cities`)
          required: true
          schema: 
            id: category
            properties: 
              category: 
                type: string
                enum: ['airports', 'airlines', 'aircrafts', 'countries', 'cities']
                example: airlines
            required:
              - category
        - name: elements_static
          in: query
          description: |
            Valeur(s) de l'identifiant de la catégorie à rechercher
            - si plusieurs valeurs, les séparer par des virgules
            - si aucune valeur n'est donnée, tous les enregistrements de la catégorie sont renvoyés

            Chaque catégorie possède un seul identifiant :
            - `airports` :    airport_iata  (exemple : 'CDG')
            - `airlines` :    airline_iata  (exemple : 'AF')
            - `aircrafts` :   aircraft_icao  (exemple : 'AA')
            - `countries` :   country_iso2  (exemple : 'FR')
            - `cities` :      city_iata  (exemple : 'PAR')
          required: false
          schema:
            id: elements_static
            properties:
              elements_static:
                type: string
                description: Valeur(s) à rechercher (si vide, tous les enregistrements de la catégorie sont renvoyés)
                example: CDG,BOD,LYN
    responses:
        200:
            description: |
                Le schéma de la réponse dépend de la valeur du paramètre de requête `category`. 
                Si `category` est "aircrafts", la réponse est un objet avec les propriétés suivantes :
                - aircraft_iata
                - aircraft_icao
                - aircraft_name
                - aircraft_wiki_link

                Si `category` est "airlines", la réponse est un objet avec les propriétés suivantes :
                - airline_iata
                - airline_icao
                - airline_name

                Si `category` est "airports", la réponse est un objet avec les propriétés suivantes :
                - airport_iata
                - airport_icao
                - fk_city_iata
                - airport_name
                - airport_utc_offset_str
                - airport_utc_offset_min
                - airport_timezone_id
                - airport_latitude
                - airport_longitude
                - airport_wiki_link

                Si `category` est "cities", la réponse est un objet avec les propriétés suivantes :
                - city_iata
                - city_name
                - fk_country_iso2
                - city_utc_offset_str
                - city_utc_offset_min
                - city_timezone_id

                Si `category` est "countries", la réponse est un objet avec les propriétés suivantes :
                - country_iso2
                - country_iso3
                - country_name
                - country_numeric
                - country_wiki_link
                - country_flag
            schema:
                type: object
                properties:
                    aircraft_iata:
                        type: string
                        description: Code IATA de l'aéronef
                        example: '772'
                    aircraft_icao:
                        type: string
                        description: Code ICAO de l'aéronef
                        example: F-GUOC
                    aircraft_name:
                        type: string
                        description: Nom de l'aéronef
                        example: 'Boeing 777-200/ 200ER'
                    aircraft_wiki_link:
                        type: string
                        description: Lien Wikipedia de l'aéronef
                        example: '/wiki/Boeing_777'
                    airline_iata:
                        type: string
                        description: Code IATA de la compagnie aérienne
                        example: AF
                    airline_icao:
                        type: string
                        description: Code ICAO de la compagnie aérienne
                        example: AFR
                    airline_name:
                        type: string
                        description: Nom de la compagnie aérienne
                        example: Air France
                    airport_iata:
                        type: string
                        description: Code IATA de l'aéroport
                        example: CDG
                    airport_icao:
                        type: string
                        description: Code OACI de l'aéroport
                        example: LFPG
                    fk_city_iata:
                        type: string
                        description: Code IATA de la ville
                        example: PAR
                    airport_name:
                        type: string
                        description: Nom de l'aéroport
                        example: Charles_de_Gaulle_Airport
                    airport_utc_offset_str:
                        type: string
                        description: Fuseau horaire de l'aéroport
                        example: '+01:00'
                    airport_utc_offset_min:
                        type: number
                        description: Décalage en minutes par rapport à l'UTC pour l'aéroport
                        example: 60.0
                    airport_timezone_id:
                        type: string
                        description: ID de la zone de temps de l'aéroport
                        example: Europe/Paris
                    airport_latitude:
                        type: number
                        description: Latitude de l'aéroport
                        example: 49.0097
                    airport_longitude:
                        type: number
                        description: Longitude de l'aéroport
                        example: 2.547800
                    airport_wiki_link:
                        type: string
                        description: Lien Wikipedia de l'aéroport
                        example: '/wiki/Charles_de_Gaulle_Airport'
                    city_iata:
                        type: string
                        description: Code IATA de la ville
                        example: PAR
                    city_name:
                        type: string
                        description: Nom de la ville
                        example: Paris
                    fk_country_iso2:
                        type: string
                        description: Code ISO2 du pays
                        example: FR
                    city_utc_offset_str:
                        type: string
                        description: Fuseau horaire
                        example: '+01:00'
                    city_utc_offset_min:
                        type: number
                        description: Décalage en minutes par rapport à l'UTC
                        example: 60.0
                    city_timezone_id:
                        type: string
                        description: ID de la timezone
                        example: 'America/Chicago'
                    country_iso2:
                        type: string
                        description: Code ISO2 du pays
                        example: FR
                    country_iso3:
                        type: string
                        description: Code ISO3 du pays
                        example: FRA
                    country_name:
                        type: string
                        description: Nom du pays
                        example: France
                    country_numeric:
                        type: number
                        format: integer
                        description: Code numérique du pays
                        example: 250
                    country_wiki_link:
                        type: string
                        description: Lien Wikipedia du pays
                        example: /wiki/France
                    country_flag:
                        type: string
                        description: Drapeau du pays
                        example: '//upload.wikimedia.org/wikipedia/en/thumb/c/c3/Flag_of_France.svg/23px-Flag_of_France.svg.png'
        400:
            description: La catégorie est invalide et/ou les identifiants sont invalides
    """

    if query.category not in ['airports', 'airlines', 'aircrafts', 'countries', 'cities']:
        if query.category is None or query.category == '':
            raise BadRequest("Le nom de la catégorie est obligatoire")
        raise BadRequest("Le nom de la catégorie est invalide. Les catégories valides sont : airports, airlines, aircrafts, countries, cities.")
    if query.elements_static is not None:
        try:
            list_elements = query.elements_static.split(',')
            data_sql = get_static_data_api(query.category, elements=list_elements)
        except ValueError:
            raise BadRequest("Le champ elements_static est invalide")
    else:
        data_sql = get_static_data_api(query.category)
    return jsonify(data_sql)


@api.route('/statistic_data', methods=['GET'])
@validate()
def statistic_data(query: DataStatistic):
    """
    Retourne les données agrégées de la base de données, filtrées par date et par catégorie
    ---
    tags:
        - statistic_data
    parameters:
        - name: type_data
          in: query
          description: |
            Nom de la variable filtrée (`callsign`, `departure_airport`, `arrival_airport`, `airline`, `aircraft`, `country`, `city`)
          required: true
          schema: 
            id: type_data
            properties: 
              type_data: 
                type: string
                enum: [callsign, departure_airport, arrival_airport, airline, aircraft, country, city]
                example: airline
            required:
              - type_data
        - name: elements_statistic
          in: query
          description: |
            Valeur(s) de la catégorie spécifiée à rechercher
            - si plusieurs valeurs, les séparer par des virgules

            Chaque type de donnée possède un seul identifiant :
            - `callsign` :    callsign  (exemple : 'AFR4143'  -  Un callsign, ou numéro de vol, est constitué des 3 lettres de la compagnie + numéro de vol)
            - `departure_airport` :    dep_iata  (exemple : 'CDG')
            - `arrival_airport` :    arr_iata  (exemple : 'CDG')
            - `airline` :    airline_iata  (exemple : 'AF')
            - `aircraft` :   aircraft_icao  (exemple : 'AA')
            - `country` :   country_iso2  (exemple : 'FR')
            - `city` :      city_iata  (exemple : 'PAR')
          required: True
          schema:
            id: elements_statistic
            properties:
              elements_statistic:
                type: string
                description: Valeur(s) à rechercher
                example: CDG,BOD,LYN
            required:
              - elements_statistic
        - name: date_data
          in: query
          description: |
            Date en chaîne de caractères, de la forme AAAA-MM-JJ (exemple : '2020-12-05')

            REMARQUE : 
            La durée de rétention des données est de 7 jours maximum. 
            Vous ne devez donc pas indiquer :
            - ni une date antérieure à 7 jours
            - ni une date ultérieure à la date actuelle
          required: false
          schema:
            id: date_data
            properties:
              date_data:
                type: string
                description: Date à rechercher
                example: "2020-12-05"
    responses:
        200:
            description: |
                Données agrégées par numéro de vol et filtrées : 
                - par date (optionnel)
                - par type de données (obligatoire)

            schema:
                type: object
                properties:
                    callsign:
                        type: string
                        description: Numéro de vol
                        example: AF6739
                    time_start:
                        type: integer
                        description: Time du départ au format time_unix (format int64)
                        example: 1684331702
                    datetime_start:
                        type: string
                        format: date-time
                        description: Date et heure de départ
                        example: '2023-05-17T15:55:02'
                    time_end:
                        type: integer
                        description: Heure d'arrivée (format int64)
                        example: 1684336202
                    datetime_end:
                        type: string
                        format: date-time
                        description: Date et heure d'arrivée
                        example: '2023-05-17T17:10:02'
                    count:
                        type: integer
                        description: Nombre d'enregistrement réalisés pour le vol
                        example: 26
                    airline_iata:
                        type: string
                        description: Code IATA de la compagnie aérienne
                        example: AF
                    arr_iata:
                        type: string
                        description: Code IATA de l'aéroport d'arrivée
                        example: CDG
                    arr_icao:
                        type: string
                        description: Code ICAO de l'aéroport d'arrivée
                        example: LFPG
                    dep_iata:
                        type: string
                        description: Code IATA de l'aéroport de départ
                        example: ORD
                    dep_icao:
                        type: string
                        description: Code ICAO de l'aéroport de départ
                        example: KORD
                    aircraft_flag:
                        type: string
                        description: Code ISO2 du pays d'origine de l'aéronef
                        example: FR
                    aircraft_reg_number:
                        type: string
                        description: Numéro d'enregistrement de l'aéronef
                        example: F-GUOC
                    aircraft_icao:
                        type: string
                        description: Code ICAO de l'aéronef
                        example: B77L
                    date_data:
                        type: string
                        format: date
                        description: Date séléectionnée des données à récupérer
                        example: '2023-05-17'
                    aircraft_iata:
                        type: string
                        description: Code IATA de l'aéronef
                        example: '772'
                    aircraft_name:
                        type: string
                        description: Nom de l'aéronef
                        example: 'Boeing 777-200/ 200ER'
                    aircraft_wiki_link:
                        type: string
                        description: Lien Wikipedia de l'aéronef
                        example: '/wiki/Boeing_777'
                    airline_icao:
                        type: string
                        description: Code ICAO de la compagnie aérienne
                        example: AFR
                    airline_name:
                        type: string
                        description: Nom de la compagnie aérienne
                        example: Air France
                    dep_fk_city_iata:
                        type: string
                        description: Code IATA de la ville de départ
                        example: CHI
                    dep_airport_name:
                        type: string
                        description: Nom de l'aéroport de départ
                        example: O'Hare International Airport
                    dep_airport_utc_offset_str:
                        type: string
                        description: Fuseau horaire de l'aéroport de départ
                        example: '-06:00'
                    dep_airport_utc_offset_min:
                        type: number
                        description: Décalage en minutes par rapport à l'UTC pour l'aéroport de départ
                        example: -360.0
                    dep_airport_timezone_id:
                        type: string
                        description: ID de la timezone de l'aéroport de départ
                        example: 'America/Chicago'
                    dep_airport_latitude:
                        type: number
                        description: Latitude de l'aéroport de départ
                        example: 41.9786
                    dep_airport_longitude:
                        type: number
                        description: Longitude de l'aéroport de départ
                        example: -87.9047
                    dep_airport_wiki_link:
                        type: string
                        description: Lien Wikipedia de l'aéroport de départ
                        example: '/wiki/OHare_International_Airport'
                    dep_city_name:
                        type: string
                        description: Nom de la ville de départ
                        example: Chicago
                    dep_country_name:
                        type: string
                        description: Nom du pays de départ
                        example: United States Of America
                    dep_country_iso3:
                        type: string
                        description: Code ISO3 du pays de départ
                        example: USA
                    dep_country_iso2:
                        type: string
                        description: Code ISO2 du pays de départ
                        example: US
                    dep_country_flag:
                        type: string
                        description: Drapeau du pays de départ
                        example: '//upload.wikimedia.org/wikipedia/en/thumb/a/a4/Flag_of_the_United_States.svg/23px-Flag_of_the_United_States.svg.png'
                    dep_country_wiki_link:
                        type: string
                        description: Lien Wikipedia du pays de départ
                        example: '/wiki/United_States'
                    arr_fk_city_iata:
                        type: string
                        description: Code IATA de la ville d'arrivée
                        example: PAR
                    arr_airport_name:
                        type: string
                        description: Nom de l'aéroport d'arrivée
                        example: Charles_de_Gaulle_Airport
                    arr_airport_utc_offset_str:
                        type: string
                        description: Fuseau horaire de l'aéroport d'arrivée
                        example: '+01:00'
                    arr_airport_utc_offset_min:
                        type: number
                        description: Décalage en minutes par rapport à l'UTC pour l'aéroport d'arrivée
                        example: 60.0
                    arr_airport_timezone_id:
                        type: string
                        description: ID de la timezone de l'aéroport d'arrivée
                        example: Europe/Paris
                    arr_airport_latitude:
                        type: number
                        description: Latitude de l'aéroport d'arrivée
                        example: 49.0097
                    arr_airport_longitude:
                        type: number
                        description: Longitude de l'aéroport d'arrivée
                        example: 2.547800
                    arr_airport_wiki_link:
                        type: string
                        description: Lien Wikipedia de l'aéroport d'arrivée
                        example: '/wiki/Charles_de_Gaulle_Airport'
                    arr_city_name:
                        type: string
                        description: Nom de la ville d'arrivée
                        example: Paris
                    arr_country_name:
                        type: string
                        description: Nom du pays d'arrivée
                        example: France
                    arr_country_iso3:
                        type: string
                        description: Code ISO3 du pays d'arrivée
                        example: FRA
                    arr_country_iso2:
                        type: string
                        description: Code ISO2 du pays d'arrivée
                        example: FR
                    arr_country_flag:
                        type: string
                        description: Drapeau du pays d'arrivée
                        example: '//upload.wikimedia.org/wikipedia/en/thumb/c/c3/Flag_of_France.svg/23px-Flag_of_France.svg.png'
                    arr_country_wiki_link:
                        type: string
                        description: Lien Wikipedia du pays d'arrivée
                        example: /wiki/France
        400:
            description: |
              Le type de données est invalide (Les valeurs valides sont : callsign, departure_airport, arrival_airport, airline, aircraft, country, city)
              Le champ elements est invalide (Si vous recherchez plusieurs valeurs, les séparer par des virgules - ex: CDG,BOD,LYN)
              La date est invalide (La date doit être de la forme AAAA-MM-JJ et doit être au maximum antérieure à 7 jours)
        404:
            description: |
              Aucun enregistrement correspondant à la requête n'a été trouvé. Modifier la requête et essayer à nouveau
    """

    if query.type_data not in ['callsign', 'departure_airport', 'arrival_airport', 'airline', 'aircraft', 'country', 'city']:
        if query.type_data is None or query.type_data == "":
            raise BadRequest("Le champ type_data est obligatoire")
        raise BadRequest("La variable d'agrégation n'est pas valide. Les variables valides sont : callsign, departure_airport, arrival_airport, airline, aircraft, country, city.")
    else:
        if query.elements_statistic is None or query.elements_statistic == "":
            raise BadRequest("Le champ elements_statistic est obligatoire")
        try:
            list_elements = query.elements_statistic.split(',')
        except ValueError:
            raise BadRequest("Le champ elements_statistic est invalide")

        if query.date_data is not None:
            test_date = validate_date(query.date_data)
            if test_date != "ok":
                if test_date == "date_incorrect_format":
                    raise BadRequest("La date n'est pas de la forme AAAA-MM-JJ")
                elif test_date == "date_no_valid":
                    raise BadRequest("La date n'est pas une date valide")
                elif test_date == "date_out_of_range":
                    raise BadRequest("La date est antérieure à 7 jours ou postérieure à la date actuelle")
            df_stats = get_data_statistics(date_data=query.date_data)
        else:
            df_stats = get_data_statistics()

        data = get_data_statistics_type_data_api(df_stats, dic_var_stats[query.type_data], list_elements)
        if len(data) == 0:
            raise NotFound("Aucun enregistrement correspondant à la requête n'a été trouvé. Modifier la requête et essayer à nouveau")

    return jsonify(data)

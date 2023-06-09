from flask import Blueprint, jsonify, request, make_response
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
from pydantic import BaseModel, ValidationError, validator, Field
from flask_pydantic import validate
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
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

# Gestion d'une erreur d'authentification (401)
@api.errorhandler(401)
def unauthorized(e):
    return jsonify(error=str("L'utilisateur n'est pas authentifié")), 401

# Gestion d'une erreur de permissions suffisantes (403)
@api.errorhandler(403)
def forbidden(e):
    return jsonify(error=str("L'utilisateur n'a pas les droits suffisants pour accéder au modèle demandé")), 403


# ----------------------------------------------
# Dictionnaires de conversion
# ----------------------------------------------

dic_var_stats = {
    'callsign': 'callsign',
    'departure_airport': 'dep_iata',
    'arrival_airport': 'arr_iata',
    'airline': 'airline_iata',
    'aircraft': 'aircraft_iata',
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

class Flight(BaseModel):
    "Class permettant de récuperer les données dynamiques des vols en direct sur la Map"
    callsign: Optional[str] = None
    dep_airport: Optional[str] = None
    arr_airport: Optional[str] = None
    airline: Optional[str] = None
    country: Optional[str] = None

class Callsign(BaseModel):
    "Class permettant de récuperer les positons d'un vol en particulier"
    callsign: str

class Airport(BaseModel):
    "Class permettant de récuperer les positons d'un vol en particulier"
    airport: str

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
        - Static Data
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
            - `aircrafts` :   aircraft_iata  (exemple : 'AAA')
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
                        description: Code ICAO de l'aéroport
                        example: LFPG
                    fk_city_iata:
                        type: string
                        description: Code IATA de la ville
                        example: PAR
                    airport_name:
                        type: string
                        description: Nom de l'aéroport
                        example: Charles de Gaulle Airport
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
                        description: ID de la timezone de l'aéroport
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
        404:
            description: Aucun enregistrement ne correspond à la requête
    """

    if query.category not in ['airports', 'airlines', 'aircrafts', 'countries', 'cities']:
        if query.category is None or query.category == '':
            raise BadRequest("Le nom de la catégorie est obligatoire")
        raise BadRequest("Le nom de la catégorie est invalide. Les catégories valides sont : airports, airlines, aircrafts, countries, cities.")
    if query.elements_static is not None:
        try:
            list_elements = query.elements_static.split(',')
            data_sql = get_static_data_api(query.category, elements=list_elements)
            if data_sql is None or len(data_sql) == 0:
                raise NotFound("Aucun enregistrement ne correspond à la requête")
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
        - Statistic Data
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
            - `aircraft` :   aircraft_iata  (exemple : 'AAA')
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
        raise BadRequest("La catégorie spécifiée n'est pas valide. Les catégories valides sont : callsign, departure_airport, arrival_airport, airline, aircraft, country, city.")
    else:
        if query.elements_statistic is None or query.elements_statistic == "":
            raise BadRequest("Le champ elements_statistic est obligatoire")
        try:
            list_elements = query.elements_statistic.split(',')
            list_elements = [x.strip().upper() for x in list_elements]
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
        if data is None:
            raise NotFound("Aucun enregistrement correspondant à la requête n'a été trouvé. Modifier la requête et essayer à nouveau")

    return jsonify(data)



#####################################################################
#  ROUTES ADMIN
#####################################################################

# ROUTE ADMIN LOGIN


class Admin(BaseModel):
    """Class permettant d'authentifier l'utilisateur Admin"""
    username: str
    password: str

@api.route('/login', methods=['POST'])
def login():
    """
    Création d'un token d'authentification pour l'utilisateur Admin
    ---
    tags:
        - Admin
    parameters:
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
              username:
                type: string
                description: Admin Username
              password:
                type: string
                description: Admin Password
            required: 
              - username
              - password
    responses:
        200:
            description: L'utilisateur est authentifié
            schema:
                type: object
                properties:
                    access_token:
                        type: string
                        description: le token d'authentification
                        example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
        400:
            description: Les champs username et password sont obligatoires
        401:
            description: L'utilisateur n'est pas authentifié
    """
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    # Données de connexion de l'utilisateur Admin
    LOG_ADMIN = os.environ.get('ADMIN_LOGIN_API')
    PASS_ADMIN = os.environ.get('ADMIN_PASSWORD_API')

    # Vérification de la connexion
    if username is None or password is None:
        return jsonify(error="Les champs username et password sont obligatoires"), 400
    elif username != LOG_ADMIN or password != PASS_ADMIN:
        return jsonify(error="L'utilisateur Admin n'est pas authentifié"), 401
    else:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    return jsonify(error="Une erreur inattendue s'est produite"), 500


# -------------------------------------------------------------
# Table airlines
# -------------------------------------------------------------

# Route pour ajouter une compagnie aérienne
###########################################
class AirlineInsert(BaseModel):
    """Class AirlineInsert permettant d'ajouter une compagnie aérienne"""
    airline_iata: str = Field(..., description="Le code IATA de la compagnie aérienne.")
    airline_icao: Optional[str] = Field(None, description="Le code ICAO de la compagnie aérienne.")
    airline_name: Optional[str] = Field(None, description="Le nom de la compagnie aérienne.")

@api.route('/airlines', methods=['POST'])
@jwt_required()
def create_airline():
    """
    Ajouter une compagnie aérienne
    ---
    tags:
        - Airlines Admin
    parameters:
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
              airline_iata:
                type: string
                description: Code IATA de la compagnie aérienne
                example: AF
                minLength: 2
                maxLength: 2
                pattern: ^[A-Z0-9]{2}$
              airline_icao:
                type: string
                description: Code ICAO de la compagnie aérienne
                example: AFR
                minLength: 3
                maxLength: 3
                pattern: ^[A-Z]{3}$
                nullable: true
              airline_name:
                type: string
                description: Nom de la compagnie aérienne
                example: Air France
                nullable: true
                maxLength: 255
            required: 
              - airline_iata
    responses:
        201:
            description: La compagnie aérienne a bien été ajoutée
        400:
            description: |
                Le champs airline_iata est obligatoire
                Les données sont invalides (Les champs à renseigner sont : airline_iata, airline_icao, airline_name)
        403:
            description: |
                Vous n'êtes pas autorisé à ajouter une compagnie aérienne
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à créer une compagnie aérienne
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification des données envoyées
        data = request.get_json()
        data_keys_send = list(data.keys())
        airline = AirlineInsert(**data)
        dict_airline = airline.dict()
        keys_invalids = list(set(data_keys_send) - set(dict_airline.keys()))
        if len(keys_invalids) > 0:
            return jsonify(error="Les données sont invalides (Les champs à renseigner sont : airline_iata, airline_icao, airline_name)"), 400
        if len(dict_airline) != 0:
            airline_iata = dict_airline.get('airline_iata', None)
            airline_iata = airline_iata.upper() if airline_iata is not None else None

            # Vérification de la présence de la clé primaire
            if airline_iata is None or airline_iata == "":
                return jsonify(error="Le champ 'airline_iata' est obligatoire"), 400
            test_add = admin_api('airlines', 'post', data=dict_airline)
            result = list(test_add.keys())[0]
            if result == 'error':
                return jsonify(test_add), 400
            else:
                return jsonify(dict_airline), 201
        else:
            return jsonify(error="Aucune donnée envoyée"), 400
    else:
        return jsonify(error="Vous n'êtes pas autorisé à ajouter une compagnie aérienne"), 403


# Route pour modifier une compagnie aérienne
############################################

class AirlineUpdate(BaseModel):
    """Class AirlineUpdate permettant de modifier une compagnie aérienne"""
    airline_icao: Optional[str] = Field(None, description="Le code ICAO de la compagnie aérienne.")
    airline_name: Optional[str] = Field(None, description="Le nom de la compagnie aérienne.")

@api.route('/airlines/<airline_iata>', methods=['PUT'])
@jwt_required()
def update_airline(airline_iata):
    """
    Modifier une compagnie aérienne
    ---
    tags:
        - Airlines Admin
    parameters:
        - in: path
          name: airline_iata
          required: true
          description: Code IATA de la compagnie aérienne
          type: string
          pattern: ^[A-Z0-9]{2}$
          example: AF
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
              airline_icao:
                type: string
                description: Code ICAO de la compagnie aérienne
                example: AFR
                minLength: 3
                maxLength: 3
                pattern: ^[A-Z]{3}$
                nullable: true
              airline_name:
                type: string
                description: Nom de la compagnie aérienne
                example: Air France
                nullable: true
                maxLength: 255
    responses:
        200:
            description: La compagnie aérienne a bien été modifiée
        400:
            description: |
                Le champs airline_iata est obligatoire
                Les données sont invalides (Les champs à renseigner sont : airline_iata, airline_icao, airline_name)
        403:
            description: |
                Vous n'êtes pas autorisé à modifier une compagnie aérienne
        404:
            description: |
                Aucun enregistrement trouvé avec ce code IATA
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à modifier la compagnie aérienne
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification de la présence du code_iata dans le path de la requête
        if airline_iata is None or airline_iata == "":
            return jsonify(error="Le champ 'airline_iata' est obligatoire"), 400

        # Vérification de la présence du code_iata en base de données
        test_code_iata = check_primary_key("airlines", "airline_iata", airline_iata)
        airline_iata = airline_iata.upper()
        if test_code_iata is False:
            data = request.get_json()
            data_keys_send = list(data.keys())
            airline = AirlineUpdate(**data)
            dict_airline = airline.dict()
            keys_invalids = list(set(data_keys_send) - set(dict_airline.keys()))
            if len(keys_invalids) > 0:
                return jsonify(error="Les données sont invalides (Les champs à renseigner sont : airline_iata, airline_icao, airline_name)"), 400

            # Vérification des données envoyées
            if len(data) != 0:
                test_update = admin_api('airlines', 'put', data=dict_airline, pk_value=airline_iata)
                result = list(test_update.keys())[0]
                if result == 'error':
                    return jsonify(test_update), 400
                else:
                    dict_result = {k:v for k, v in dict_airline.items() if v is not None}
                    return jsonify(dict_result), 200
            else:
                return jsonify(error="Aucune donnée envoyée"), 400
        else:
            return jsonify(error="Aucun enregistrement trouvé avec ce code IATA"), 404
    else:
        return jsonify(error="Vous n'êtes pas autorisé à modifier une compagnie aérienne"), 403



# Route pour supprimer une compagnie aérienne
############################################

@api.route('/airlines/<airline_iata>', methods=['DELETE'])
@jwt_required()
def delete_airline(airline_iata):
    """
    Supprimer une compagnie aérienne
    ---
    tags:
        - Airlines Admin
    parameters:
        - in: path
          name: airline_iata
          required: true
          description: Code IATA de la compagnie aérienne
          type: string
          pattern: ^[A-Z0-9]{2}$
          example: AF
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
    responses:
        204:
            description: La compagnie aérienne a bien été supprimée
        400:
            description: |
                Le champs airline_iata est obligatoire
        403:
            description: |
                Vous n'êtes pas autorisé à supprimer une compagnie aérienne
        404:
            description: |
                Aucun enregistrement trouvé avec ce code IATA
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à supprimer la compagnie aérienne
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification de la présence du code_iata dans le path de la requête
        if airline_iata is None or airline_iata == "":
            return jsonify(error="Le champ 'airline_iata' est obligatoire"), 400

        # Vérification de la présence du code_iata en base de données
        airline_iata = airline_iata.upper()
        test_code_iata = check_primary_key("airlines", "airline_iata", airline_iata)
        if test_code_iata is False:

            # Suppression de la compagnie aérienne
            test_delete = admin_api('airlines', 'delete', pk_value=airline_iata)
            result = list(test_delete.keys())[0]
            if result == 'error':
                return jsonify(test_delete), 400
            else:
                return '', 204

        else:
            return jsonify(error="Aucun enregistrement trouvé avec ce code IATA"), 404
    else:
        return jsonify(error="Vous n'êtes pas autorisé à supprimer une compagnie aérienne"), 403




# -------------------------------------------------------------
# Table aircrafts
# -------------------------------------------------------------

# Route pour ajouter un avion
#############################
class AircraftInsert(BaseModel):
    """Class AircraftInsert permettant d'ajouter un avion"""
    aircraft_iata: str = Field(..., description="Le code IATA de l'avion.")
    aircraft_icao: Optional[str] = Field(None, description="Le code ICAO de l'avion.")
    aircraft_name: Optional[str] = Field(None, description="Le nom de l'avion.")
    aircraft_wiki_link: Optional[str] = Field(None, description="Le lien vers la page Wikipedia.")

@api.route('/aircrafts', methods=['POST'])
@jwt_required()
def create_aircraft():
    """
    Ajouter un avion
    ---
    tags:
        - Aircrafts Admin
    parameters:
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
              aircraft_iata:
                type: string
                description: Code IATA de l'avion
                example: 320
                minLength: 3
                maxLength: 3
                pattern: ^[A-Z0-9]{3}$
                nullable: false
              aircraft_icao:
                type: string
                description: Code ICAO de l'avion
                example: A320
                minLength: 4
                maxLength: 4
                pattern: ^[A-Z0-9]{4}$
                nullable: true
              aircraft_name:
                type: string
                description: Nom de l'avion
                example: Airbus A320
                nullable: true
                maxLength: 255
              aircraft_wiki_link:
                type: string
                description: Lien vers la page Wikipedia
                example: '/wiki/Airbus_A320'
                nullable: true
                maxLength: 255
            required: 
              - aircraft_iata
    responses:
        201:
            description: L'avion a bien été ajouté
        400:
            description: |
                Le champs aircraft_iata est obligatoire
                Les données sont invalides (Les champs à renseigner sont : aircraft_iata, aircraft_icao, aircraft_name, aircraft_wiki_link)
        403:
            description: |
                Vous n'êtes pas autorisé à ajouter un avion
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à créer un avion
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification des données envoyées
        data = request.get_json()
        data_keys_send = list(data.keys())
        aircraft = AircraftInsert(**data)
        dict_aircraft = aircraft.dict()
        keys_invalids = list(set(data_keys_send) - set(dict_aircraft.keys()))
        if len(keys_invalids) > 0:
            return jsonify(error="Les données sont invalides (Les champs à renseigner sont : aircraft_iata, aircraft_icao, aircraft_name, aircraft_wiki_link)"), 400

        if len(data) != 0:
            aircraft_iata = dict_aircraft.get('aircraft_iata', None)
            aircraft_iata = aircraft_iata.upper() if aircraft_iata is not None else None

            # Vérification de la présence de la clé primaire
            if aircraft_iata is None or aircraft_iata == "":
                return jsonify(error="Le champ 'aircraft_iata' est obligatoire"), 400
            test_add = admin_api('aircrafts', 'post', data=dict_aircraft)
            result = list(test_add.keys())[0]
            if result == 'error':
                return jsonify(test_add), 400
            else:
                return jsonify(dict_aircraft), 201
        else:
            return jsonify(error="Aucune donnée envoyée"), 400
    else:
        return jsonify(error="Vous n'êtes pas autorisé à ajouter un avion"), 403


# Route pour modifier un avion
############################################
class AircraftUpdate(BaseModel):
    """Class AircraftUpdate permettant de modifier un avion"""
    aircraft_icao: Optional[str] = Field(None, description="Le code ICAO de l'avion.")
    aircraft_name: Optional[str] = Field(None, description="Le nom de l'avion.")
    aircraft_wiki_link: Optional[str] = Field(None, description="Le lien vers la page Wikipedia.")

@api.route('/aircrafts/<aircraft_iata>', methods=['PUT'])
@jwt_required()
def update_aircraft(aircraft_iata):
    """
    Modifier un avion
    ---
    tags:
        - Aircrafts Admin
    parameters:
        - in: path
          name: aircraft_iata
          required: true
          description: Code IATA de l'avion
          type: string
          example: 320
          format: string
          pattern: ^[A-Z0-9]{3}$
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
              aircraft_icao:
                type: string
                description: Code ICAO de l'avion
                example: A320
                minLength: 4
                maxLength: 4
                pattern: ^[A-Z0-9]{4}$
                nullable: true
              aircraft_name:
                type: string
                description: Nom de l'avion
                example: Airbus A320
                nullable: true
                maxLength: 255
              aircraft_wiki_link:
                type: string
                description: Lien vers la page Wikipedia
                example: '/wiki/Airbus_A320'
                nullable: true
                maxLength: 255
    responses:
        200:
            description: L'avion a bien été modifié
        400:
            description: |
                Le champs aircraft_iata est obligatoire
                Les données sont invalides (Les champs à renseigner sont : aircraft_iata, aircraft_icao, aircraft_name, aircraft_wiki_link)
        403:
            description: |
                Vous n'êtes pas autorisé à modifier un avion
        404:
            description: |
                Aucun enregistrement trouvé avec ce code IATA
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à modifier l'avion
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification de la présence du code_iata dans le path de la requête
        if aircraft_iata is None or aircraft_iata == "":
            return jsonify(error="Le champ 'aircraft_iata' est obligatoire"), 400

        # Vérification de la présence du code_iata en base de données
        aircraft_iata = aircraft_iata.upper()
        test_code_iata = check_primary_key("aircrafts", "aircraft_iata", aircraft_iata)
        if test_code_iata is False:
            data = request.get_json()
            data_keys_send = list(data.keys())
            aircraft = AircraftUpdate(**data)
            dict_aircraft = aircraft.dict()
            keys_invalids = list(set(data_keys_send) - set(dict_aircraft.keys()))
            if len(keys_invalids) > 0:
                return jsonify(error="Les données sont invalides (Les champs à renseigner sont : aircraft_iata, aircraft_icao, aircraft_name, aircraft_wiki_link)"), 400

            # Vérification des données envoyées
            if len(data) != 0:
                test_update = admin_api('aircrafts', 'put', data=dict_aircraft, pk_value=aircraft_iata)
                result = list(test_update.keys())[0]
                if result == 'error':
                    return jsonify(test_update), 400
                else:
                    dict_result = {k:v for k, v in dict_aircraft.items() if v is not None}
                    return jsonify(dict_result), 200
            else:
                return jsonify(error="Aucune donnée envoyée"), 400
        else:
            return jsonify(error="Aucun enregistrement trouvé avec ce code IATA"), 404
    else:
        return jsonify(error="Vous n'êtes pas autorisé à modifier un avion"), 403


# Route pour supprimer un avion
############################################

@api.route('/aircrafts/<aircraft_iata>', methods=['DELETE'])
@jwt_required()
def delete_aircraft(aircraft_iata):
    """
    Supprimer un avion
    ---
    tags:
        - Aircrafts Admin
    parameters:
        - in: path
          name: aircraft_iata
          required: true
          description: Code IATA de l'avion
          type: string
          example: AF
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
    responses:
        204:
            description: L'avion a bien été supprimé
        400:
            description: |
                Le champs aircraft_iata est obligatoire
        403:
            description: |
                Vous n'êtes pas autorisé à supprimer un avion
        404:
            description: |
                Aucun enregistrement trouvé avec ce code IATA
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à supprimer l'avion
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification de la présence du code_iata dans le path de la requête
        if aircraft_iata is None or aircraft_iata == "":
            return jsonify(error="Le champ 'aircraft_iata' est obligatoire"), 400

        # Vérification de la présence du code_iata en base de données
        aircraft_iata = aircraft_iata.upper()
        test_code_iata = check_primary_key("aircrafts", "aircraft_iata", aircraft_iata)
        if test_code_iata is False:

            # Suppression de l'avion
            test_delete = admin_api('aircrafts', 'delete', pk_value=aircraft_iata)
            result = list(test_delete.keys())[0]
            if result == 'error':
                return jsonify(test_delete), 400
            else:
                return '', 204

        else:
            return jsonify(error="Aucun enregistrement trouvé avec ce code IATA"), 404
    else:
        return jsonify(error="Vous n'êtes pas autorisé à supprimer un avion"), 403




# -------------------------------------------------------------
# Table airports
# -------------------------------------------------------------

# Route pour ajouter un aéroport
#############################
class AirportInsert(BaseModel):
    """Class AirportInsert permettant d'ajouter un aéroport"""
    airport_iata: str = Field(..., description="Le code IATA de l'aéroport.")
    airport_icao: Optional[str] = Field(None, description="Le code ICAO de l'aéroport.")
    fk_city_iata: str = Field(..., description="Le code IATA de la ville de l'aéroport.")
    airport_name: Optional[str] = Field(None, description="Le nom de l'aéroport.")
    airport_utc_offset_str: Optional[str] = Field(None, description="Fuseau horaire de l'aéroport.")
    airport_utc_offset_min: Optional[int] = Field(None, description="Décalage en minutes par rapport à l'UTC.")
    airport_timezone_id: Optional[str] = Field(None, description="Id de la timezone de l'aéroport.")
    airport_latitude: Optional[float] = Field(None, description="Latitude de l'aéroport.")
    airport_longitude: Optional[float] = Field(None, description="Longitude de l'aéroport.")
    airport_wiki_link: Optional[str] = Field(None, description="Le lien vers la page Wikipedia.")

@api.route('/airports', methods=['POST'])
@jwt_required()
def create_airport():
    """
    Ajouter un aéroport
    ---
    tags:
        - Airports Admin
    parameters:
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
              airport_iata:
                type: string
                description: Code IATA de l'aéroport
                example: CDG
                minLength: 3
                maxLength: 3
                pattern: ^[A-Z]{3}$
                nullable: false
              airport_icao:
                type: string
                description: Code ICAO de l'aéroport
                example: LFPG
                minLength: 4
                maxLength: 4
                pattern: ^[A-Z]{4}$
                nullable: true
              fk_city_iata:
                type: string
                description: |
                  Code IATA de la ville de l'aéroport
                  Remarque : le code IATA de la ville doit être présent dans la table cities.
                  (vous pouvez vérifier son existence en utilisant la méthode `GET` la route `/static_data`, avec le paramètre `category=cities`) 
                example: PAR
                minLength: 3
                maxLength: 3
                pattern: ^[A-Z]{3}$
                nullable: false
              airport_name:
                type: string
                description: Nom de l'aéroport
                example: Charles de Gaulle Airport
                nullable: true
                maxLength: 255
              airport_utc_offset_str:
                type: string
                description: Fuseau horaire de l'aéroport
                example: '+01:00'
                maxLength: 20
                nullable: true
              airport_utc_offset_min:
                type: integer
                description: Décalage en minutes par rapport à l'UTC
                example: 60
                nullable: true
              airport_timezone_id:
                type: string
                description: Id de la timezone de l'aéroport
                example: 'Europe/Paris'
                maxLength: 100
                nullable: true
              airport_latitude:
                type: number
                format: float
                description: Latitude de l'aéroport
                example: 49.0097
                nullable: true
                min: -90
                max: 90
              airport_longitude:
                type: number
                format: float
                description: Longitude de l'aéroport
                example: 2.5478
                nullable: true
                min: -180
                max: 180
              airport_wiki_link:
                type: string
                description: Lien vers la page Wikipedia
                example: '/wiki/Charles_de_Gaulle_Airport'
                nullable: true
                maxLength: 255
            required: 
              - [airport_iata, fk_city_iata]
    responses:
        201:
            description: L'aéroport a bien été ajouté
        400:
            description: |
                Les champs airport_iata et fk_city_iata sont obligatoires
                Les données sont invalides (Les champs à renseigner sont : airport_iata, airport_icao, fk_city_iata, airport_name, airport_utc_offset_str, airport_utc_offset_min, airport_timezone_id, airport_latitude, airport_longitude, airport_wiki_link)
        403:
            description: |
                Vous n'êtes pas autorisé à ajouter un aéroport
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à créer un aéroport
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification des données envoyées
        data = request.get_json()
        data_keys_send = list(data.keys())
        airport = AirportInsert(**data)
        dict_airport = airport.dict()
        keys_invalids = list(set(data_keys_send) - set(dict_airport.keys()))
        if len(keys_invalids) > 0:
            return jsonify(error="Les données sont invalides (Les champs à renseigner sont : airport_iata, airport_icao, fk_city_iata, airport_name, airport_utc_offset_str, airport_utc_offset_min, airport_timezone_id, airport_latitude, airport_longitude, airport_wiki_link)"), 400

        if len(data) != 0:
            airport_iata = dict_airport.get('airport_iata', None)
            airport_iata = airport_iata.upper() if airport_iata is not None else None
            fk_city_iata = dict_airport.get('fk_city_iata', None)
            fk_city_iata = fk_city_iata.upper() if fk_city_iata is not None else None

            # Vérification de la présence de la clé primaire
            if airport_iata is None or airport_iata == "":
                return jsonify(error="Le champ 'airport_iata' est obligatoire"), 400

            # Vérification de la présence de fk_city_iata
            if fk_city_iata is None or fk_city_iata == "":
                return jsonify(error="Le champ 'fk_city_iata' est obligatoire"), 400

            # Vérification de la présence de fk_city_iata dans la table cities
            test_fk = check_primary_key("cities", "city_iata", fk_city_iata)
            if test_fk is False:
                test_add = admin_api('airports', 'post', data=dict_airport)
                result = list(test_add.keys())[0]

                if result == 'error':
                    return jsonify(test_add), 400
                else:
                    return jsonify(dict_airport), 201
            else:
                return jsonify(error="Le code IATA de la ville de l'aéroport n'est pas présent dans la table 'cities'"), 401
        else:
            return jsonify(error="Aucune donnée envoyée"), 400
    else:
        return jsonify(error="Vous n'êtes pas autorisé à ajouter un aéroport"), 403


# Route pour modifier un aéroport
############################################
class AirportUpdate(BaseModel):
    """Class AirportUpdate permettant de modifier un aéroport"""
    airport_icao: Optional[str] = Field(None, description="Le code ICAO de l'aéroport.")
    fk_city_iata: Optional[str] = Field(None, description="Le code IATA de la ville de l'aéroport.")
    airport_name: Optional[str] = Field(None, description="Le nom de l'aéroport.")
    airport_utc_offset_str: Optional[str] = Field(None, description="Fuseau horaire de l'aéroport.")
    airport_utc_offset_min: Optional[int] = Field(None, description="Décalage en minutes par rapport à l'UTC.")
    airport_timezone_id: Optional[str] = Field(None, description="Id de la timezone de l'aéroport.")
    airport_latitude: Optional[float] = Field(None, description="Latitude de l'aéroport.")
    airport_longitude: Optional[float] = Field(None, description="Longitude de l'aéroport.")
    airport_wiki_link: Optional[str] = Field(None, description="Le lien vers la page Wikipedia.")

@api.route('/airports/<airport_iata>', methods=['PUT'])
@jwt_required()
def update_airport(airport_iata):
    """
    Modifier un aéroport
    ---
    tags:
        - Airports Admin
    parameters:
        - in: path
          name: airport_iata
          required: true
          description: Code IATA de l'aéroport
          type: string
          example: CDG
          format: string
          pattern: ^[A-Z]{3}$
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
              airport_icao:
                type: string
                description: Code ICAO de l'aéroport
                example: LFPG
                minLength: 4
                maxLength: 4
                pattern: ^[A-Z]{4}$
                nullable: true
              fk_city_iata:
                type: string
                description: |
                  Code IATA de la ville de l'aéroport
                  Remarque : le code IATA de la ville doit être présent dans la table cities.
                  (vous pouvez vérifier son existence en utilisant la méthode `GET` la route `/static_data`, avec le paramètre `category=cities`) 
                example: PAR
                minLength: 3
                maxLength: 3
                pattern: ^[A-Z]{3}$
                nullable: false
              airport_name:
                type: string
                description: Nom de l'aéroport
                example: Charles de Gaulle Airport
                nullable: true
                maxLength: 255
              airport_utc_offset_str:
                type: string
                description: Fuseau horaire de l'aéroport
                example: '+01:00'
                maxLength: 20
                nullable: true
              airport_utc_offset_min:
                type: integer
                description: Décalage en minutes par rapport à l'UTC
                example: 60
                nullable: true
              airport_timezone_id:
                type: string
                description: Id de la timezone de l'aéroport
                example: 'Europe/Paris'
                maxLength: 100
                nullable: true
              airport_latitude:
                type: number
                format: float
                description: Latitude de l'aéroport
                example: 49.0097
                nullable: true
                min: -90
                max: 90
              airport_longitude:
                type: number
                format: float
                description: Longitude de l'aéroport
                example: 2.5478
                nullable: true
                min: -180
                max: 180
              airport_wiki_link:
                type: string
                description: Lien vers la page Wikipedia
                example: '/wiki/Charles_de_Gaulle_Airport'
                nullable: true
                maxLength: 255
    responses:
        200:
            description: L'aéroport a bien été modifié
        400:
            description: |
                Le champs airport_iata est obligatoire
                Les données sont invalides (Les champs à renseigner sont : airport_iata, airport_icao, fk_city_iata, airport_name, airport_utc_offset_str, airport_utc_offset_min, airport_timezone_id, airport_latitude, airport_longitude, airport_wiki_link)
        403:
            description: |
                Vous n'êtes pas autorisé à modifier un aéroport
        404:
            description: |
                Aucun enregistrement trouvé avec ce code IATA
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à modifier l'aéroport
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification de la présence du code_iata dans le path de la requête
        if airport_iata is None or airport_iata == "":
            return jsonify(error="Le champ 'airport_iata' est obligatoire"), 400

        # Vérification de la présence du code_iata en base de données
        airport_iata = airport_iata.upper()
        test_code_iata = check_primary_key("airports", "airport_iata", airport_iata)
        if test_code_iata is False:

            data = request.get_json()
            data_keys_send = list(data.keys())
            airport = AirportUpdate(**data)
            dict_airport = airport.dict()
            keys_invalids = list(set(data_keys_send) - set(dict_airport.keys()))
            if len(keys_invalids) > 0:
                return jsonify(error="Les données sont invalides (Les champs à renseigner sont : airport_iata, airport_icao, fk_city_iata, airport_name, airport_utc_offset_str, airport_utc_offset_min, airport_timezone_id, airport_latitude, airport_longitude, airport_wiki_link)"), 400

            # Vérification des données envoyées
            if len(data) != 0:
                # Vérification de la présence de fk_city_iata dans le body de la requête
                fk_city_iata = dict_airport.get('fk_city_iata', None)
                # Si fk_city_ita est renseigné, alors on vérifie son existence dans la table cities
                if fk_city_iata is not None:
                    fk_city_iata = fk_city_iata.upper()
                    test_fk = check_primary_key("cities", "city_iata", fk_city_iata)
                    if test_fk is True:
                        return jsonify(error="Le code IATA de la ville de l'aéroport n'est pas présent dans la table 'cities'"), 401
                else:
                    # on récupère la valeur de fk_city_iata en base de données
                    fk_city_iata = get_value_pk_airports(airport_iata)
                    if fk_city_iata is None:
                        return jsonify(error="Aucun enregistrement trouvé avec ce code IATA"), 404
                    dict_airport['fk_city_iata'] = fk_city_iata
                test_update = admin_api('airports', 'put', data=dict_airport, pk_value=airport_iata)
                result = list(test_update.keys())[0]
                if result == 'error':
                    return jsonify(test_update), 400
                else:
                    dict_result = {k:v for k, v in dict_airport.items() if v is not None}
                    return jsonify(dict_result), 200
            else:
                return jsonify(error="Aucune donnée envoyée"), 400
        else:
            return jsonify(error="Aucun enregistrement trouvé avec ce code IATA"), 404
    else:
        return jsonify(error="Vous n'êtes pas autorisé à modifier un aéroport"), 403



# Route pour supprimer un aéroport
############################################

@api.route('/airports/<airport_iata>', methods=['DELETE'])
@jwt_required()
def delete_airport(airport_iata):
    """
    Supprimer un aéroport
    ---
    tags:
        - Airports Admin
    parameters:
        - in: path
          name: airport_iata
          required: true
          description: Code IATA de l'aéroport
          type: string
          example: CDG
        - in: header
          name: Authorization
          required: true
          type: string
          description: |
            Token d'authentification (Saisir : Bearer + [token])

            Vous pouvez générer un token d'authentification à partir de la route `/login` en méthode `POST` en saisissant votre username et votre password.
          type: string
          format: Bearer
          example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJS
    responses:
        204:
            description: L'aéroport a bien été supprimé
        400:
            description: |
                Le champs airport_iata est obligatoire
        403:
            description: |
                Vous n'êtes pas autorisé à supprimer un aéroport
        404:
            description: |
                Aucun enregistrement trouvé avec ce code IATA
    """
    current_user = get_jwt_identity()

    # Vérification que l'utilisateur est autorisé à supprimer l'aéroport
    if current_user == os.environ.get('ADMIN_LOGIN_API'):

        # Vérification de la présence du code_iata dans le path de la requête
        if airport_iata is None or airport_iata == "":
            return jsonify(error="Le champ 'airport_iata' est obligatoire"), 400

        # Vérification de la présence du code_iata en base de données
        airport_iata = airport_iata.upper()
        test_code_iata = check_primary_key("airports", "airport_iata", airport_iata)
        if test_code_iata is False:

            # Suppression de l'aéroport
            test_delete = admin_api('airports', 'delete', pk_value=airport_iata)
            result = list(test_delete.keys())[0]
            if result == 'error':
                return jsonify(test_delete), 400
            else:
                return '', 204

        else:
            return jsonify(error="Aucun enregistrement trouvé avec ce code IATA"), 404
    else:
        return jsonify(error="Vous n'êtes pas autorisé à supprimer un aéroport"), 403
    

# Route - Liste de tous les avions en vol à l'instant T, en Europe
############################################
@api.get('/flights')
@validate()
def get_flights(query: Flight):
    """
    Retourne le(s) vol(s) à l'instant de la requête en Europe
    ---
    tags:
        - Dynamic data
    parameters:
        - name: callsign
          in: query
          description: |
            Callsign de l'appareil
            Exemple: AFR1234
          required: false
        - name: dep_airport
          in: query
          description: |
            Aéroport de départ de l'aéronef
            Exemple: CDG
          required: false
        - name: arr_airport
          in: query
          description: |
            Aéroport d'arrivé de l'aéronef
            Example: BDO
          required: false
        - name: airline
          in: query
          description: |
            Compagnie aérienne de l'aéronef
            Exemple: Air France
          required: false
        - name: country
          in: query
          description: |
            Pays d'origine de l'aéronef (en anglais)
            Exemple: France
          required: false
    responses:
        200:
            description: |
                La réponse est une liste d'objet JSON (données de chaque appareil) avec les propriétés suivantes :
                - airline_company, la compagnie aérienne de l'aéronef
                - arrival_airport, aéroport d'arrivé
                - baro_altitude, l'altitude barométrique de l'aéronef
                - callsign, le callsign de l'aéronef
                - cap, le cap de l'aéronef
                - datatime, date de l'enregistrement des données de vol d'un aéronef
                - depart_airport, aéroport de départ
                - flight_number, le numéro de vol de l'aéronef
                - geo_altitude, l'altitude géographique de l'aéronef
                - latitude, la latitude de l'aéronef
                - longitude, la longitude de l'aéronef
                - on_ground, si l'aéronef est au sol (hangar, aéroport ...) ou en vol
                - origin_country, pays d'origine de l'aéronef
                - origin_country_code, code pays d'origine de l'aéronef
                - velocity, la vitesse de l'aéronef          
                - vertical_rate, la vitesse d'ascencion, ou de déscente de l'aéronef
        404:
            description: |
                Aucun vol correspondant aux paramètres entrés dans l'URL n'a été trouvé dans note base de donnée.
    """
    flights = get_flights_api(query.callsign, query.dep_airport, query.arr_airport, query.airline, query.country)
    if flights == '404':
        raise NotFound(f"Aucun vol correspondant aux paramètres entrés dans l'URL n'a été trouvé dans note base de donnée.")
        
    return jsonify(flights), 200

# Liste de toutes les positions de vols d'un appareil
@api.get('/flight/positions')
@validate()
def get_positions(query: Callsign):
    """
    Retourne les positions d'un vol du jour
    ---
    tags:
        - Dynamic data
    parameters:
        - name: callsign
          in: query
          description: |
            Callsign de l'appareil
            Exemple: AFR1234
          required: true
    responses:
        200:
            description: |
                Retourne les positions de vol d'un aéronef
                - airline_iata, code iata de la compagnie aérienne (3 caractères alphabétiques)
                - arr_iata, aéroport d'arrivé
                - baro_altitude, l'altitude barométrique
                - callsign, callsign de l'aéronef
                - cap, le cap
                - datatime, date de prise de la mesure
                - dep_iata, aéroport d'arrivé
                - flag, code pays de l'aéronef
                - latitude, la latitude de l'aéronef
                - longitude, la longitutude de l'aéronef
                - on_ground, si l'appareil est au sol ou en vol
                - origin_country, pays d'origine de l'appareil
                - velocity, vitesse de l'appareil
                - vertical_rate, vitesse ascencionnelle ou de déscente de l'aéronef
        400:
            description: |
                Veuillez entrer un callsign valide, et réessayer.
        404:
            description: |
                Aucun vol correspondant aux paramètres entrés dans l'URL n'a été trouvé dans note base de donnée.
    """
    if not query.callsign:
        raise BadRequest("Veuillez entrer un callsign valide, et réessayer.")


    positions = get_flight_positions(query.callsign, api=True)
    if not positions:
        raise NotFound("Aucun vol n'a été trouvé dans notre base de données.")
    

    return jsonify(positions), 200

# Liste des aéroports les plus désservis à partir d'un aéroport de départ
@api.get('/airports')
@validate()
def get_airports(query: Airport):
    """
    Retourne les aéroports les plus desservis à partir d'un aérport de départ
    ---
    tags:
        - Dynamic data
    parameters:
        - name: airport
          in: query
          description: |
            Aéroport de départ
            Exemple: CDG
          required: true
    responses:
        200:
            description: |
                Retourne les aéroports les plus desservis à partir d'un aérport de départ (y compris l'aéroport de départ en premiere position)
                - airport_iata, code aéroport à 3 caractères alphabétiques
                - airport_latitude, la latitude de l'aéroport
                - airport_longitude, la longitude de l'aéroport
        400:
            description: |
                Veuillez entrer un code aéroport valide, et réessayer.
        404:
            description: |
                Aucune donnée n'a été trouvée dans notre base de donnée.
    """
    if not query.airport:
        raise BadRequest("Veuillez entrer un code aéroport valide, et réessayer.")
    
    try:
        airports = get_datas(query.airport)

    except:
        raise BadRequest("Veuillez entrer un code aéroport valide, et réessayer.")

    return jsonify(airports), 200

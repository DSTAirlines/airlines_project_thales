import requests
from sqlalchemy.orm import Session
import string
import itertools
import random, json, os, sys
from pathlib import Path
import dotenv
from datetime import datetime, timezone
dotenv.load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent.parent)

# Importer la fonction de connexion à MySQL
sys.path.append(f"{parent_dir}/connect_database")
from connection_sql import get_connection as connection_mysql

# Importer les fichiers de l'application Dash
sys.path.append(f"{parent_dir}/appli_dash")
from models import Airline, Aircraft, Airport, City, Country
from get_data import *


# Présence du content des responses dans le fichier log
CONTENT_LOG=os.environ.get('TESTS_API_LOG_CONTENT_RESPONSE')


# informations d'identification
credentials = {
    'username': os.environ.get('ADMIN_LOGIN_API'),
    'password': os.environ.get('ADMIN_PASSWORD_API')
}

# Base URL API
BASE_URL = "http://localhost:8050/api/v1/"

# Credentials Administrateur
user_admin = os.environ.get('ADMIN_LOGIN_API')
user_password = os.environ.get('ADMIN_PASSWORD_API')

# Suppression d'un éventuel fichier de test
try:
    os.remove('tests_api.log')
except FileNotFoundError:
    pass

now_utc = datetime.now(timezone.utc)
now_utc_str = now_utc.strftime("%H")
now_local = now_utc.astimezone()
now_local_str = now_local.strftime("%H")

today = datetime.today()
datetime_str = today.strftime("%Y-%m-%d %H:%M:%S")
if now_utc_str == now_local_str:
    datetime_str += " UTC"
insert_datetime = f'''
####################################################
#  Tests réalisés le {datetime_str}
####################################################
'''

global recap 
recap = {
    "nb_tests": 0,
    "nb_tests_ok": 0,
    "nb_tests_ko": 0,
    "test_failed": []
}


with open('tests_api.log', 'a', encoding='utf-8') as file:
    file.write(insert_datetime)


def get_list_values_pk(table):
    """
    Fonction permettant de récupérer la liste des valeurs primaires d'une table
    Args:
        table (str): Nom de la table dont on veut récupérer la liste des valeurs primaires
    Return: 
        list: liste des valeurs primaires de la table
    """
    
    # Etablir la connection à la base SQL
    engine = connection_mysql()
    # Créer une session
    session = Session(engine)

    # Sélectionner toutes les valeurs prises par la PK de la table 'table'
    if table == "airlines":
        elements = session.query(Airline.airline_iata).all()
    elif table == "aircrafts":
        elements = session.query(Aircraft.aircraft_iata).all()
    elif table == "airports":
        elements = session.query(Airport.airport_iata).all()
    elif table == "cities":
        elements = session.query(City.city_iata).all()
    else:
        elements = None

    # Fermez la session
    session.close()

    if elements is not None:
        # Convertir la liste de tuples en liste de valeurs:
        elements = [el[0] for el in elements]
        random.shuffle(elements)

    return elements


def get_random_available_element(table):
    """
    Renvoie une valeur aléatoire pour la PK de la table 'table' non présent en bdd
    Args:
        table (str): Nom de la table
    Returns:
        str: valeur aléatoire non présente de la PK de la table
    """

    # Récupérer la liste des valeurs de la Primary Key de la table
    elements = get_list_values_pk(table)

    LETTERS = string.ascii_uppercase
    LETTERS_DIGITS = string.ascii_uppercase + string.digits

    def random_id(input_pattern, nb_iter, list_iata=elements):
        all_combinations = [''.join(combination) for combination in itertools.product(input_pattern, repeat=nb_iter)]
        available_iata = list(set(all_combinations) - set(list_iata))
        random.shuffle(available_iata)
        if len(available_iata) > 0:
            return available_iata[0]
        return None

    if elements is not None:
        # Sélectionner une valeur aléatoire pour la PK de la table 'table' non présente dans la bdd
        if table == "airlines":
            iata_id = random_id(LETTERS_DIGITS, 2)
        elif table == "aircrafts":
            iata_id = random_id(LETTERS_DIGITS, 3)
        elif table == "airports" or table == "cities":
            iata_id = random_id(LETTERS, 3)
    
    return iata_id



def test_get_static(category, code_expected, elements_static=None):
    """
    Teste la méthodes GET de l'endpoint static_data
    """

    global recap
    url = f"{BASE_URL}static_data"

    headers = {
        'Content-Type': 'application/json'
    }

    params = {
        'category': category
    }
    if elements_static is not None:
        params['elements_static'] = elements_static

    r = requests.get(f"{url}", headers=headers, params=params)
    status_code = r.status_code
    response_content = r.text
    try:
        dict_response = json.loads(response_content)
        json_response = json.dumps(dict_response, ensure_ascii=False)
    except json.JSONDecodeError:
        json_response = "Invalid JSON response: " + response_content

    recap['nb_tests'] += 1
    if status_code == code_expected:
        test_status = "SUCCES"
        recap['nb_tests_ok'] += 1
    else:
        test_status = "FAIL"
        recap['nb_tests_ko'] += 1
        recap['test_failed'].append({
            "category": category,
            "elements_static": elements_static,
            "code_expected": code_expected,
            "status_code": status_code,
            "response_content": response_content
        })

    output = '''
============================
   GET /static_data
============================

| category = {category}
| elements_static = {elements_static}


| expected result = {code_expected}
| actual result = {status_code}

############################
==>  {test_status}
############################

'''
    if CONTENT_LOG == '1':
        output += '''
response_content = {response_content}

'''
    output +='''
-----------------------------
'''
    formatted_output = output.format(
        category=category,
        elements_static=elements_static,
        code_expected=code_expected,
        status_code=status_code,
        test_status=test_status,
        response_content=json_response
    )

    with open('tests_api.log', 'a', encoding='utf-8') as file:
        file.write(formatted_output)



def test_get_statistic(type_data, elements_statistic, code_expected, date_data=None):
    """
    Teste la méthodes GET de l'endpoint statistic_data
    """
    global recap
    url = f"{BASE_URL}statistic_data"

    headers = {
        'Content-Type': 'application/json'
    }

    params = {
        'type_data': type_data,
        'elements_statistic': elements_statistic
    }
    if date_data is not None:
        params['date_data'] = date_data

    r = requests.get(f"{url}", headers=headers, params=params)

    status_code = r.status_code
    response_content = r.text
    try:
        dict_response = json.loads(response_content)
        json_response = json.dumps(dict_response, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        json_response = "Invalid JSON response: " + response_content

    recap['nb_tests'] += 1
    if status_code == code_expected:
        test_status = "SUCCES"
        recap['nb_tests_ok'] += 1
    else:
        test_status = "FAIL"
        recap['nb_tests_ko'] += 1
        recap['test_failed'].append({
            "type_data": type_data,
            "elements_statistic": elements_statistic,
            "date_data": date_data,
            "code_expected": code_expected,
            "status_code": status_code,
            "response_content": response_content
        })

    output = '''
============================
   GET /static_data
============================

| type_data = {type_data}
| elements_statistic = {elements_statistic}
| date_data = {date_data}


| expected result = {code_expected}
| actual result = {status_code}

############################
==>  {test_status}
############################

'''
    if CONTENT_LOG == '1':
        output += '''
response_content = {response_content}

'''
    output +='''
-----------------------------
'''
    formatted_output = output.format(
        type_data=type_data,
        elements_statistic=elements_statistic,
        date_data=date_data,
        code_expected=code_expected,
        status_code=status_code,
        test_status=test_status,
        response_content=json_response
    )

    with open('tests_api.log', 'a', encoding='utf-8') as file:
        file.write(formatted_output)



def test_connect_admin(username, password, correct=True):
    """
    Teste la connexion d'un administrateur
    """

    global recap
    credentials = {
        'username': username,
        'password': password
    }

    if correct:
        u_name = "ADMIN_USERNAME"
        u_pass = "ADMIN_PASSWORD"
        u_code = 200
    else:
        u_name = "FALSE_USERNAME"
        u_pass = "FALSE_PASSWORD"
        u_code = 401

    output = '''
============================
   Authentification test
============================

request done at "/login"
| username =     {u_name}
| password =     {u_pass}

expected result = {u_code}
actual result = {status_code}

############################
==>  {test_status}
############################

response_content = {response_content}

-----------------------------
'''
    req = requests.post(f"{BASE_URL}login", json=credentials)
    status_code = req.status_code
    response_content = req.text
    try:
        dict_response = json.loads(response_content)
        json_response = json.dumps(dict_response, ensure_ascii=False)
    except json.JSONDecodeError:
        json_response = "Invalid JSON response: " + response_content

    recap['nb_tests'] += 1
    if status_code == u_code:
        test_status = "SUCCES"
        recap['nb_tests_ok'] += 1
    else:
        test_status = "FAIL"
        recap['nb_tests_ko'] += 1
        recap['test_failed'].append({
            "username": username,
            "password": password,
            "code_expected": u_code,
            "status_code": status_code,
            "response_content": response_content
        })

    formatted_output = output.format(
        u_name=u_name,
        u_pass=u_pass,
        u_code=u_code,
        status_code=status_code,
        response_content=json_response,
        test_status=test_status
    )

    with open('tests_api.log', 'a') as file:
        file.write(formatted_output)
    return formatted_output


def connection_admin():
    """
    Obtenir le token d'authentification
    """

    credentials = {
        'username': user_admin,
        'password': user_password
    }

    # Requête POST à la route /login
    req = requests.post(f"{BASE_URL}login", json=credentials)

    # Récupération du token
    token = req.json().get('access_token')

    if token:
        return token
    return None


def test_admin(table, method, code_expected, titre, id=None, data=None):
    """
    Teste les méthodes POST, PUT et DELETE des endpoints Admin de l'API
    """

    global recap
    # Obtenir le token
    token = connection_admin()
    
    # header d'authentification
    headers = {
        'Authorization': f'Bearer {token}'
    }

    if method == 'POST' or method == 'PUT':
        headers['Content-Type'] = 'application/json'
    
    if method == 'POST':
        r = requests.post(f"{BASE_URL}{table}", headers=headers, json=data)
        endpoint = table

    elif method == 'PUT':
        r = requests.put(f"{BASE_URL}{table}/{id}", headers=headers, json=data)
        endpoint = f"{table}/{id}"

    elif method == 'DELETE':
        r = requests.delete(f"{BASE_URL}{table}/{id}", headers=headers)
        endpoint = f"{table}/{id}"
    
    else:
        return None

    status_code = r.status_code
    response_content = r.text
    try:
        dict_response = json.loads(response_content)
        json_response = json.dumps(dict_response, ensure_ascii=False)
    except json.JSONDecodeError:
        json_response = "Invalid JSON response: " + response_content

    recap['nb_tests'] += 1
    if status_code == code_expected:
        test_status = "SUCCES"
        recap['nb_tests_ok'] += 1
    else:
        test_status = "FAIL"
        recap['nb_tests_ko'] += 1
        recap['test_failed'].append({
            "method": method,
            "table": table,
            "titre": titre,
            "data": data,
            "endpoint": endpoint,
            "code_expected": code_expected,
            "status_code": status_code,
            "response_content": response_content
        })

    output = '''
============================
   {method} {table}
============================
TEST = {titre}

request done at "/{endpoint}"
data send = {data}

| expected result = {code_expected}
| actual result = {status_code}

############################
==>  {test_status}
############################
'''
    if method!= 'DELETE':
        output += '''
response_content = {response_content}
'''
    output +='''
-------------------------------------------------------------------------------------
'''
    formatted_output = output.format(
        method=method,
        table=table,
        titre=titre,
        data=data,
        endpoint=endpoint,
        code_expected=code_expected,
        status_code=status_code,
        response_content=json_response,
        test_status=test_status
    )

    with open('tests_api.log', 'a', encoding='utf-8') as file:
        file.write(formatted_output)


###############################################################################
################## TEST de L'API - DONNEES DYNAMIQUES #########################
###############################################################################

def recap_tests():
    """
    Récapitulatif des tests
    """

    global recap
    output = '''
===========================================
|    Récapitulatif des tests
===========================================
| Nombre de tests effectués : {nb_tests}
| Nombre de tests réussis   : {nb_tests_ok}
| Nombre de tests échoués   : {nb_tests_ko}
'''
    if recap['nb_tests_ko'] > 0:
        output += '''
| Tests échoués : {test_failed}
'''
    output += '''===========================================
'''

    formatted_output = output.format(
        nb_tests=recap['nb_tests'],
        nb_tests_ok=recap['nb_tests_ok'],
        nb_tests_ko=recap['nb_tests_ko'],
        test_failed=recap['test_failed']
    )

    with open('tests_api.log', 'a', encoding='utf-8') as file:
        file.write(formatted_output)
    
    print(formatted_output)
    recap = {
        'nb_tests': 0,
        'nb_tests_ok': 0,
        'nb_tests_ko': 0,
        'test_failed': []
    }
    
def test_airports_api():
    """Test la route /airports"""
    url = f"{BASE_URL}airports"

    headers = {
        'Content-Type': 'application/json'
    }

    # test de l'API avec un aéroport de départ fixé, ici CDG (Charles de Gaulles)
    params = {
        'airport': 'CDG',
    }

    r = requests.get(f"{url}", headers=headers, params=params)

    status_code = r.status_code
    response_content = r.text
    try:
        dict_response = json.loads(response_content)
        json_response = json.dumps(dict_response, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        json_response = "Invalid JSON response: " + response_content

    recap['nb_tests'] += 1
    if status_code == 200:
        test_status = "SUCCES"
        recap['nb_tests_ok'] += 1
    else:
        test_status = "FAIL"
        recap['nb_tests_ko'] += 1
        recap['test_failed'].append(
            {
                "airport": 'CDG',
                "code_expected": 200,
                "status_code": status_code,
                "response_content": response_content
            }
        )

    output = '''
============================
GET /airports
============================

| airport = CDG

| expected result = 200
| actual result = {status_code}

############################
==>  {test_status}
############################

'''
    if CONTENT_LOG == '1':
        output += '''
response_content = {response_content}

'''
        output +='''
-------------------------------------------------------------------------------------
'''
    formatted_output = output.format(
        status_code=status_code,
        test_status=test_status,
        response_content=json_response
    )

    with open('tests_api.log', 'a', encoding='utf-8') as file:
        file.write(formatted_output)


def test_flight_positons_api():
    """Test la route /flight/positions"""
    url = f"{BASE_URL}flight/positions"

    headers = {
        'Content-Type': 'application/json'
    }

    r = requests.get(f"{url}", headers=headers)

    status_code = r.status_code
    response_content = r.text
    try:
        dict_response = json.loads(response_content)
        json_response = json.dumps(dict_response, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        json_response = "Invalid JSON response: " + response_content

    # On a pas forcément de callsign valide au moment du test, donc on test l'echec de l'appel à l'API comme un succès.
    recap['nb_tests'] += 1
    if status_code == 400:
        test_status = "SUCCES"
        recap['nb_tests_ok'] += 1
    else:
        test_status = "FAIL"
        recap['nb_tests_ko'] += 1
        recap['test_failed'].append(
            {
                "code_expected": 400,
                "status_code": status_code,
                "response_content": response_content
            }
        )

    output = '''
============================
GET /flight/positions
============================

| callsign = None

| expected result = 400
| actual result = {status_code}

############################
==>  {test_status}
############################

'''
    if CONTENT_LOG == '1':
        output += '''
response_content = {response_content}

'''
        output +='''
-------------------------------------------------------------------------------------
'''
    formatted_output = output.format(
        status_code=status_code,
        test_status=test_status,
        response_content=json_response
    )

    with open('tests_api.log', 'a', encoding='utf-8') as file:
        file.write(formatted_output)

# Vols en direct de la carte de l'Europe (Map Live)
def test_flights_api():
    """Test de la route /flights"""
    
    global recap
    url = f"{BASE_URL}flights"

    headers = {
        'Content-Type': 'application/json'
    }

    params = {
        'dep_airport': 'CDG'
    }

    r = requests.get(f"{url}", headers=headers, params=params)

    status_code = r.status_code
    response_content = r.text
    try:
        dict_response = json.loads(response_content)
        json_response = json.dumps(dict_response, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        json_response = "Invalid JSON response: " + response_content

    recap['nb_tests'] += 1
    if status_code == 200:
        test_status = "SUCCES"
        recap['nb_tests_ok'] += 1
    else:
        test_status = "FAIL"
        recap['nb_tests_ko'] += 1
        recap['test_failed'].append(
            {
                "dep_airport": 'CDG',
                "code_expected": 200,
                "status_code": status_code,
                "response_content": response_content
            }
        )

    output = '''
============================
GET /flights
============================

| airport = CDG

| expected result = 200
| actual result = {status_code}

############################
==>  {test_status}
############################

'''
    if CONTENT_LOG == '1':
        output += '''
response_content = {response_content}

'''
        output +='''
-------------------------------------------------------------------------------------
'''
    formatted_output = output.format(
        status_code=status_code,
        test_status=test_status,
        response_content=json_response
    )

    with open('tests_api.log', 'a', encoding='utf-8') as file:
        file.write(formatted_output)
from datetime import datetime, timedelta
from functions_tests_api import *

########################################################################
#
#   Possibilité d'afficher ou non le contenu des responses
#   des requêtes des méthodes GET via la variable 
#   d'environnement TESTS_API_LOG_CONTENT_RESPONSE
#
#########################################################################



# --------------------------------------
# TEST STATIC_DATA
# --------------------------------------

# CORRECT DATA
test_get_static('airports', 200, elements_static="CDG,BOD")

# INCORRECT DATA - BAD CATEGORY
test_get_static('aeroports', 400)

# INCORRECT DATA - ELEMENT_NOT_FOUND
iata_available = get_random_available_element('airlines')
test_get_static('airlines', 404, elements_static=iata_available)



# --------------------------------------
# TEST STATISTIC_DATA
# --------------------------------------

today = datetime.today()
date_ok = today - timedelta(days=1)
date_ok_str = date_ok.strftime("%Y-%m-%d")
date_out = today - timedelta(days=20)
date_out_str = date_out.strftime("%Y-%m-%d")

# CORRECT DATA
test_get_statistic("departure_airport", "CDG,BDO", 200, date_data=date_ok_str)

# INCORRECT DATA - BAD TYPE_DATA
test_get_statistic("aeroport_de_depart", "CDG", 400, date_data=None)

# INCORRECT DATA - DATE OUT OF RANGE
test_get_statistic("arrival_airport", "CDG,BDO", 400, date_data=date_out_str)

# INCORRECT DATA - DATE BAD FORMAT
test_get_statistic("airline", "AFR", 400, date_data="02-12-2022")

# INCORRECT DATA - ELEMENT_NOT_FOUND (elements_statistic)
iata_available = get_random_available_element('airlines')
test_get_statistic("airline", iata_available, 404, date_data=None)




###########################################################################
#   TESTS ADMIN
###########################################################################


# --------------------------------------
# TEST AUTHENTIFICATION ADMIN
# --------------------------------------
auth_true = test_connect_admin(user_admin, user_password)
auth_false = test_connect_admin("user_test", "password_test", correct=False)



# --------------------------------------
# TEST ADMIN AIRLINES
# --------------------------------------

# CORRECT DATA - METHOD POST
available_iata = get_random_available_element('airlines')
data = {
    'airline_iata': available_iata,
    'airline_icao': 'ZZZ',
    'airline_name': 'Test Airline Name',
}
test_admin('airlines', 'POST', 201, 'CORRECT DATA - METHOD POST', data=data)

# CORRECT DATA - METHOD PUT
data = {
    'airline_name': 'Test Airline New Name',
}
test_admin('airlines', 'PUT', 200, 'CORRECT DATA - METHOD PUT', id=available_iata, data=data)

# CORRECT DATA - METHOD DELETE
test_admin('airlines', 'DELETE', 204, 'CORRECT DATA - METHOD DELETE', id=available_iata)


# INCORRECT DATA - METHOD POST - Test 1
iata_not_availble = get_list_values_pk('airlines')[0]
data = {
    'airline_iata': iata_not_availble,
    'airline_icao': 'ZZZ',
    'airline_name': 'Test Airline Name'
}
test_admin('airlines', 'POST', 400, 'INCORRECT DATA - METHOD POST - Test 1', data=data)

# INCORRECT DATA - METHOD POST - Test 2
iata_available = get_random_available_element('airlines')
data = {
    'airline_iata': iata_available,
    'airline_icao': 'ZZZ',
    'airline_bad_field': 'Test Airline Bad Field'
}
test_admin('airlines', 'POST', 400, 'INCORRECT DATA - METHOD POST - Test 2', data=data)

# INCORRECT DATA - METHOD PUT
data = {
    'airline_name': 'Test Airline New Name'
}
test_admin('airlines', 'PUT', 404, 'INCORRECT DATA - METHOD PUT', id=iata_available, data=data)

# INCORRECT DATA - METHOD DELETE
test_admin('airlines', 'DELETE', 404, 'INCORRECT DATA - METHOD DELETE', id=iata_available)



# --------------------------------------
# TEST ADMIN AIRCRAFTS
# --------------------------------------

# CORRECT DATA - METHOD POST
available_iata = get_random_available_element('aircrafts')
data = {
    'aircraft_iata': available_iata,
    'aircraft_icao': 'ZZZZ',
    'aircraft_name': 'Test Aircraft Name',
    'aircraft_wiki_link': '/wiki/Test Aircraft Name'
}
test_admin('aircrafts', 'POST', 201, 'CORRECT DATA - METHOD POST', data=data)

# CORRECT DATA - METHOD PUT
data = {
    'aircraft_icao': 'BBBB',
}
test_admin('aircrafts', 'PUT', 200, 'CORRECT DATA - METHOD PUT', id=available_iata, data=data)

# CORRECT DATA - METHOD DELETE
test_admin('aircrafts', 'DELETE', 204, 'CORRECT DATA - METHOD DELETE', id=available_iata)


# INCORRECT DATA - METHOD POST - Test 1
iata_not_availble = get_list_values_pk('aircrafts')[0]
data = {
    'aircraft_iata': iata_not_availble,
    'aircraft_icao': 'ZZZ',
    'aircraft_name': 'Test Aircraft Name'
}
test_admin('aircrafts', 'POST', 400, 'INCORRECT DATA - METHOD POST - Test 1', data=data)

# INCORRECT DATA - METHOD POST - Test 2
iata_available = get_random_available_element('aircrafts')
data = {
    'aircraft_iata': iata_available,
    'aircraft_icao': 'ZZZ',
    'aircraft_bad_field': 'Test Bad Field'
}
test_admin('aircrafts', 'POST', 400, 'INCORRECT DATA - METHOD POST - Test 2', data=data)

# INCORRECT DATA - METHOD PUT
data = {
    'aircraft_name': 'Test Aircraft New Name'
}
test_admin('aircrafts', 'PUT', 404, 'INCORRECT DATA - METHOD PUT', id=iata_available, data=data)

# INCORRECT DATA - METHOD DELETE
test_admin('aircrafts', 'DELETE', 404, 'INCORRECT DATA - METHOD DELETE', id=iata_available)



# --------------------------------------
# TEST ADMIN AIRPORTS
# --------------------------------------

# CORRECT DATA - METHOD POST
available_iata = get_random_available_element('airports')
data = {
    'airport_iata': available_iata,
    'airport_icao': 'AAAA',
    'fk_city_iata': 'PAR',
    'airport_name': 'Airport Test Name',
    'airport_utc_offset_str': '+01:00',
    'airport_utc_offset_min': 60,
    'airport_timezone_id': 'Europe/Paris',
    'airport_latitude': 49.0097,
    'airport_longitude': 2.5478,
    'airport_wiki_link': '/appli_dash/woki/blalala'
}
test_admin('airports', 'POST', 201, 'CORRECT DATA - METHOD POST', data=data)

# CORRECT DATA - METHOD PUT
data = {
    'airport_icao': 'BBBB',
}
test_admin('airports', 'PUT', 200, 'CORRECT DATA - METHOD PUT', id=available_iata, data=data)

# CORRECT DATA - METHOD DELETE
test_admin('airports', 'DELETE', 204, 'CORRECT DATA - METHOD DELETE', id=available_iata)


# INCORRECT DATA - METHOD POST - Test 1
iata_not_availble = get_list_values_pk('airports')[0]
data = {
    'airport_iata': iata_not_availble,
    'airport_icao': 'AAAA',
    'fk_city_iata': 'PAR',
    'airport_name': 'Airport Test Name',
    'airport_utc_offset_str': '+01:00',
    'airport_utc_offset_min': 60,
    'airport_timezone_id': 'Europe/Paris',
    'airport_latitude': 49.0097,
    'airport_longitude': 2.5478,
    'airport_wiki_link': '/appli_dash/woki/blalala'
}
test_admin('airports', 'POST', 400, 'INCORRECT DATA - METHOD POST - Test 1', data=data)

# INCORRECT DATA - METHOD POST - Test 2
iata_available = get_random_available_element('airports')
data = {
    'airport_iata': iata_available,
    'airport_icao': 'AAAA',
    'fk_city_iata': 'PAR',
    'airport_bad_field': 'Airport Bad Field'
}
test_admin('airports', 'POST', 400, 'INCORRECT DATA - METHOD POST - Test 2', data=data)

# INCORRECT DATA - METHOD PUT - Test 1
data = {
    'airport_name': 'Test Airport New Name'
}
test_admin('airports', 'PUT', 404, 'INCORRECT DATA - METHOD PUT - Test 1', id=iata_available, data=data)

# INCORRECT DATA - METHOD PUT - Test 2
city_iata_available = get_random_available_element('cities')
data = {
    'fk_city_iata': city_iata_available,
    'airport_name': 'Test Airport New Name'
}
test_admin('airports', 'PUT', 404, 'INCORRECT DATA - METHOD PUT - Test 2', id=iata_available, data=data)

# INCORRECT DATA - METHOD DELETE
test_admin('airports', 'DELETE', 404, 'INCORRECT DATA - METHOD DELETE', id=iata_available)


# --------------------------------------
# TEST DYNAMIC DATAS
# --------------------------------------

# Appel de l'API pour les aéroports les plus desservis
test_airports_api()

# Appel de l'API pour les positions de vol d'un appareil en particulier (saisie du callsign)
test_flight_positons_api()

# RECAP TESTS
# --------------------------------------
recap_tests()


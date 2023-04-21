from functions import *
from pprint import pprint

##########################
# Test get_airport_info
##########################
print("Test de la fonction get_airport_info :")
test_airport_info = get_airport_info("CDG")
pprint(test_airport_info)

##########################
# Test get_airline_info
##########################
print("\nTest de la fonction get_airline_info :")
test_airline_info = get_airline_info("AF")
pprint(test_airline_info)

##########################
# Test get_aircraft_type
##########################
print("\nTest de la fonction get_aircraft_type :")
test_aircraft_type = get_aircraft_type("B738")
pprint(test_aircraft_type)

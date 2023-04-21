from connection_mongodb import get_connection as client_mongo
from connection_sql import get_connection as engine_sql
from sqlalchemy import create_engine, text
from pprint import pprint
from datetime import datetime
import random
import re

client = client_mongo()
db = client["liveAirlines"]
opensky = db["opensky"]
airlabs = db['airlabs']


def get_one_doc(collection):
    return collection.find_one()


def check_last_record_mongo(collection, col_callsign, col_icao24):
    list_callsigns = []
    list_icaos = []
    dic_result = {}

    # Recherche du "time" le plus récent
    max_time_result = collection.find().sort("time", -1).limit(1)
    max_time = max_time_result[0]["time"]
    dt = datetime.utcfromtimestamp(max_time).strftime('%Y-%m-%d %H:%M:%S')

    # Recherche des documents du dernier enregistrement
    cursor = collection.find({"time": max_time}, {
        "_id": 0, 
        col_callsign: 1, 
        col_icao24: 1
    })

    # Création des listes:
    for doc in cursor:
        try:
            callsign = doc[col_callsign]
            if callsign and callsign.strip() != '':
                list_callsigns.append(callsign.strip())
        except:
            continue

        try:
            icao24 = doc[col_icao24]
            if icao24 and icao24.strip() != '':
                list_icaos.append(icao24.strip())
        except:
            continue

    dic_result = {
        "datetime": dt,
        "callsigns": list_callsigns,
        "icaos": list_icaos
    }

    return dic_result


def check_correpondances_opensky_sql(list_all_callsign, list_callsing_missing):
    all_callsigns = ', '.join([f"'{callsign}'" for callsign in list_all_callsign])
    callsigns_missing = ', '.join([f"'{callsign}'" for callsign in list_callsing_missing])

    engine = engine_sql()

    # correspondances entre opensky et sql pour tous les callsigns
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM routes WHERE callsign IN ({all_callsigns})"))
        print(f"\nNb de Routes correspondant à tous les callsigns d'OpenSky: {len(result.all())}")

    # correspondances entre opensky et sql pour les callsigns non présents dans airlabs
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM routes WHERE callsign IN ({callsigns_missing})"))
        print(f"Nb de Routes trouvées correspondant aux callsigns non présents dans Airlabs: {len(result.all())}\n")


def get_one_flight_details(callsign_target):

    opensky_docs = [] 
    airlabs_doc = None

    # Les callsigns enregistrés peuvent comporter des espaces en trop à la fin
    callsign_regex = re.compile(f"^{callsign_target}\\s*$", re.IGNORECASE)

    # API OpenSky
    # -----------

    # Recherche du "time" le plus récent
    max_time_result = opensky.find().sort("time", -1).limit(1)
    max_time = max_time_result[0]["time"]

    # Itération par time décroissant
    cursor = opensky.find({"call_sign": {"$regex": callsign_regex}, "time": {"$lte": max_time}}).sort("time", -1)

    # On collecte les documents
    for doc in cursor:
        opensky_docs.append(doc)

        # On vérifie si le callsign est présent dans le document avec le "time" précédent
        current_time = doc["time"]
        previous_doc = opensky.find_one({"call_sign": {"$regex": callsign_regex}, "time": {"$lt": current_time}}, sort=[("time", -1)])

        if not previous_doc:
            break

    # API AirLabs
    # -----------

    # Recherche du "time" le plus récent
    max_time_res_airlabs = airlabs.find().sort("time", -1).limit(1)
    max_time_airlabs = max_time_res_airlabs[0]["time"]

    cursor = airlabs.find({
        "time": max_time_airlabs,
        "flight_icao": callsign_target
    }).limit(1)

    airlabs_docs = list(cursor)
    if len(airlabs_docs) != 0:
        airlabs_doc = airlabs_docs[0]

    dic_result = {
        "docs_opensky": opensky_docs,
        "doc_airlabs": airlabs_doc
    }

    return dic_result



# Collection OpenSky
res_opensky = check_last_record_mongo(opensky, "call_sign", "icao_24")
nb_callsigns_opensky = len(res_opensky['callsigns'])
nb_icaos24_opensky = len(res_opensky['icaos'])
print(f"\nRésultat OpenSky : \n - datetime UTC : {res_opensky['datetime']}\n - Nb callsign : {nb_callsigns_opensky}\n - Nb icao24 : {nb_icaos24_opensky}")

# Collection Airlabs
res_airlabs = check_last_record_mongo(airlabs, "flight_icao", "hex")
nb_callsigns_airlabs = len(res_airlabs['callsigns'])
nb_icaos24_airlabs = len(res_airlabs['icaos'])
print(f"\nRésultat AirLabs : \n - datetime UTC : {res_airlabs['datetime']}\n - Nb callsign : {nb_callsigns_airlabs}\n - Nb icao24 : {nb_icaos24_airlabs}")

# Check des correspondances entre OpenSky et Airlabs
callsigns_communs = list(set(res_opensky['callsigns']) & set(res_airlabs['callsigns']))
callsigns_missing = list(set(res_opensky['callsigns']) - set(callsigns_communs))
icaos_communs = list(set(res_opensky['icaos']) & set(res_airlabs['icaos']))
print(f"\nCorrespondances entre les 2 collections : \n - Nb callsign communs : {len(callsigns_communs)}\n - Nb icao24 communs : {len(icaos_communs)}")

# Check des correspondances entre OpenSky et base MySQL
check_correpondances_opensky_sql(res_opensky['callsigns'], callsigns_missing)

# Test d'un vol en random
random_number = random.randint(0, len(res_opensky['callsigns'])-1)
test_callsign = res_opensky['callsigns'][random_number]
res_one_flight = get_one_flight_details(test_callsign)
print(f"\nRésultat pour le détail d'un vol random callsign : {test_callsign}")
print(f"- Résultat OpenSky : ")
print(f" - Nb de docs : {len(res_one_flight['docs_opensky'])}")
last_doc = res_one_flight['docs_opensky'][-1]
last_time = last_doc["time"]
dt = datetime.utcfromtimestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')
print(f" - Datetime UTC 1er doc : {dt}")
print()
print(f"\n - Résultat Airlabs : ")
print(res_one_flight['doc_airlabs'])

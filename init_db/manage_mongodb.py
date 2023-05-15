import sys
import os
from pathlib import Path
from pymongo import ASCENDING as asc
from pymongo import DESCENDING as desc
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection

# Ajout du path des appels API
sys.path.append(f"{parent_dir}/live_api")
# Importer la fonction d'appel à l'API airlabs
from fetch_airlabs_data import lauch_script as airlabs_api
# Importer la fonction d'appel à l'API opensky
from fetch_opensky_data import lauch_script as opensky_api


# Credentials
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")


# Test du succes de la creation de la base de données
# ---------------------------------------------------
def test_crud_collection(collection):

    # Insérer un document dans la collection
    insert_result = collection.insert_one({"key": "value"})

    # Vérifier si l'insertion a réussi
    if insert_result.acknowledged:
        print(" - Insertion réussie du document")
    else:
        print("Erreur lors de l'insertion du document")

    # Récupérer le document inséré et l'afficher
    document = collection.find_one({"key": "value"})
    print(" - Document trouvé:", document)

    # Supprimer le document de test (nettoyage)
    try:
        collection.delete_one({"key": "value"})
        print(" - Document correctement supprimé\n")
    except:
        print("Erreur lors de la suppression du document")


# Création de la base de données MongoDB
# --------------------------------------
def create_db(db_name):
    # Etablir la connecion à la db
    client = get_connection()
    
    if db_name in client.list_database_names():
        client.drop_database(db_name)

    # Créer la base de donnée
    db = client[db_name]

    # Créer une collection "opensky" et "airlabs"
    opensky_collection = db[MONGO_COL_OPENSKY]
    airlabs_collection = db[MONGO_COL_AIRLABS]

    # Créer les index de la collection OpenSky
    opensky_collection.create_index([("time", desc), ("airlab_id", asc)])
    opensky_collection.create_index("callsign")
    opensky_collection.create_index("airlab_id")

    # Créer les index de la collection AirLabs
    airlabs_collection.create_index([("time", desc), ("flight_icao", asc)])
    airlabs_collection.create_index("flight_icao")

    for collection in [opensky_collection, airlabs_collection]:
        print(f"\nTest CRUD sur la collection {collection}")
        print('#--------------------------------')
        test_crud_collection(collection)

    # Faire d'abord un appel à opensky
    opensky_api(init=True, cron=False)
    airlabs_api(init=True, cron=False)

    # fermer la connection
    client.close()


# Drop de la base de données MongoDB
# ----------------------------------
def drop_db(db_name):
    # Etablir la connecion à la db
    client = get_connection()

    # Drop de la db
    try:
        client.drop_database(db_name)
    except Exception as ex:
        print(f"\nErreur de connexion à la database MongoDB : \n{ex}\n")
    client.close()

# drop_db(MONGO_DB_NAME)
#create_db(MONGO_DB_NAME)

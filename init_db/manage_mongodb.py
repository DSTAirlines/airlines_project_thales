import sys
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/connect_database")

# Importer le fichier de connexion à MongoDB
from connection_mongodb import get_connection

# Credentials
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_COL_AIRLABS = os.environ.get("MONGO_COL_AIRLABS")
MONGO_COL_OPENSKY = os.environ.get("MONGO_COL_OPENSKY")


# Test du succes de la creation de la base de données
# ---------------------------------------------------
def test_crud_collection(collection_name):
    # Connection à la db
    client = get_connection()

    # Créer la base de donnée
    db = client[MONGO_DB_NAME]
    collection = db[collection_name]

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

    # fermer la connection
    client.close()


# Création de la base de données MongoDB
# --------------------------------------
def create_db(db_name):
    # Etablir la connecion à la db
    client = get_connection()

    # Créer la base de donnée
    db = client[db_name]

    # Créer une collection "opensky" et "airlabs"
    opensky_collection = db[MONGO_COL_OPENSKY]
    airlabs_collection = db[MONGO_COL_AIRLABS]

    # Créer un index "fly_id" pour chaque collection
    opensky_collection.create_index("callsign")
    airlabs_collection.create_index("flight_icao")

    for collection in [MONGO_COL_OPENSKY, MONGO_COL_AIRLABS]:
        print(f"\nTest CRUD sur la collection {collection}")
        print('#--------------------------------')
        test_crud_collection(collection)

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
# create_db(MONGO_DB_NAME)
# après avoir créer la database, faire un appel à opensky PUIS à Airlabs

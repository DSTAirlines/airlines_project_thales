import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

# Credentials Database MongoDB
MONGO_HOST = os.environ.get("MONGO_HOST")
MONGO_PORT = os.environ.get("MONGO_PORT")
MONGO_DATABASE = os.environ.get("MONGO_INITDB_DATABASE")
MONGO_APP_USERNAME = os.environ.get("MONGO_INITDB_ROOT_USERNAME")
MONGO_APP_PASSWORD = os.environ.get("MONGO_INITDB_ROOT_PASSWORD")


# Retourne l'objet sqlalchemy engine
def get_connection():
    client = MongoClient(
        f"mongodb://{MONGO_HOST}:{MONGO_PORT}",
        serverSelectionTimeoutMS = 10000
    )
    print(f"mongodb://{MONGO_APP_USERNAME}:{MONGO_APP_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}")
    try:
        print(f"Connexion à la database MongoDB : {client.server_info()}")
        client.server_info()
        return client

    except Exception as ex:
        print(f"\nErreur de connexion à la database MongoDB : \n{ex}\n")
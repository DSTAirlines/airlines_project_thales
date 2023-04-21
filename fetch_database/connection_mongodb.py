import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

# Credentials Database MongoDB
MONGO_HOST = os.environ.get("MONGO_HOST")
MONGO_PORT = os.environ.get("MONGO_PORT")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PASS = os.environ.get("MONGO_PASS")

# Retourne l'objet sqlalchemy engine
def get_connection():
    client = MongoClient(
        f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}",
        serverSelectionTimeoutMS = 2000
    )
    try:
        client.server_info()
        return client

    except Exception as ex:
        print(f"\nErreur de connexion à la database MongoDB : \n{ex}\n")
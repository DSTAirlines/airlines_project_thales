from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# Credentials Database SQL
DB_HOST=os.environ.get("DB_HOST")
DB_PORT=os.environ.get("DB_PORT")
DB_NAME=os.environ.get("DB_NAME")
DB_USER=os.environ.get("DB_USER")
DB_PASS=os.environ.get("DB_PASS")

# Retourne l'objet sqlalchemy engine 
def get_connection():
    try:
        engine = create_engine(
            url="mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(
                DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
            )
        )
        print(f"\nConnexion à la database {DB_NAME} correctement réalisée.\n")
        return engine

    except Exception as ex:
        print(f"\nErreur de connexion : \n{ex}\n")

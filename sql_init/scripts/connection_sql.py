from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# Credentials Database SQL
SQL_HOST=os.environ.get("SQL_HOST")
SQL_PORT=os.environ.get("SQL_PORT")
SQL_DB_NAME=os.environ.get("SQL_DB_NAME")
SQL_USER=os.environ.get("SQL_USER")
SQL_PASS=os.environ.get("SQL_PASS")

# Retourne l'objet sqlalchemy engine 
def get_connection():
    try:
        engine = create_engine(
            url=f"mysql+pymysql://{SQL_USER}:{SQL_PASS}@{SQL_HOST}:{SQL_PORT}/{SQL_DB_NAME}"
        )
        print(f"\nConnexion à la database {SQL_DB_NAME} correctement réalisée.\n")
        return engine

    except Exception as ex:
        print(f"\nErreur de connexion : \n{ex}\n")

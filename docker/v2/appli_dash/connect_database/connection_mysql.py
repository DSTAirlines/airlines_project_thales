from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()

# Credentials Database SQL
SQL_HOST=os.environ.get("SQL_HOST")
SQL_PORT=os.environ.get("SQL_PORT")
MYSQL_DATABASE=os.environ.get("MYSQL_DATABASE")
MYSQL_USER=os.environ.get("MYSQL_ROOT_USERNAME")
MYSQL_PASSWORD=os.environ.get("MYSQL_ROOT_PASSWORD")

# Retourne l'objet sqlalchemy engine 
def get_connection():
    try:
        engine = create_engine(
            url=f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{MYSQL_DATABASE}"
        )
        return engine

    except Exception as ex:
        print(f"\nErreur de connexion : \n{ex}\n")

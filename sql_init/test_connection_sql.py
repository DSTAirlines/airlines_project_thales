from scripts.connection_sql import get_connection
from sqlalchemy import text

# Récupérer l'engine de sqlalchemy
engine = get_connection()

with engine.connect() as conn:

    # Récupérer le nom des tables
    req_get_tables = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA='Airlines_Static' 
    """
    stmt_get_tables = text(req_get_tables)
    result = conn.execute(stmt_get_tables).fetchall()

    # Pour chaque table, on affiche les 5 premiers enregistrements
    for tables in result:
        print("\n################################")
        print(f"#  Table {tables[0]} :")
        print("################################")
        req = f"SELECT * FROM {tables[0]} LIMIT 5"
        stmt = text(req)
        result = conn.execute(stmt)

        for row in result:
            print(row)

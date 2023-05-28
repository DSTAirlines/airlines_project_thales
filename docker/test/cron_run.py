from connection_mongodb import get_connection as connect_mongodb

# me connecter à la database
client = connect_mongodb()
if client:
    print("Connexion à la database MongoDB : OK")

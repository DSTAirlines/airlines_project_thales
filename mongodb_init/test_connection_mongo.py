from scripts.connection_mongodb import get_connection

# Récupérer le Client
client = get_connection()

# Choisir la base de données
db = client['liveAirlines']

# Choisir la collection
sky = db['opensky']

# Tester l'insert d'un document
insert = sky.insert_one({"key_test" : "value_test"})

# Vérifier l'insert
if insert.acknowledged:
    print("Insertion réussie")

    # Récupérer le document inséré et l'afficher
    document = sky.find_one({"key_test" : "value_test"})
    print("Document trouvé:", document)

    # Supprimer le document de test (nettoyage)
    sky.delete_one({"key": "value"})
    print("Document supprimé")

else:
    print("Erreur lors de l'insertion")

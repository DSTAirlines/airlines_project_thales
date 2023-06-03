// Connexion à la base de données
var db = db.getSiblingDB('liveAirlines');

// Création collection AirL
db.createCollection("airlabs");
const airlabs = db.getCollection("airlabs");
airlabs.createIndex({ time: -1, flight_icao: 1 });
airlabs.createIndex({ flight_icao: 1 });

// Création collection Opensky
db.createCollection("opensky");
const opensky = db.getCollection("opensky");
opensky.createIndex({ time: -1, airlab_id: 1 });
opensky.createIndex({ callsign: 1 });
opensky.createIndex({ airlab_id: 1 });


// Création collection data_aggregated
db.createCollection("data_aggregated");

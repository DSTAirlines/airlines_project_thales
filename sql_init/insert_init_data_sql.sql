USE Airlines_Static;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE countries;
TRUNCATE TABLE cities;
TRUNCATE TABLE airlines;
TRUNCATE TABLE aircrafts;
TRUNCATE TABLE airports;
SET FOREIGN_KEY_CHECKS = 1;

LOAD DATA INFILE '/var/lib/mysql-files/data_csv_init/countries.csv'
INTO TABLE countries
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(country_iso2, country_iso3, country_name, @country_numeric, country_wiki_link, country_flag)
SET country_numeric = (CASE
        WHEN @country_numeric = -1 THEN NULL
        ELSE @country_numeric
END);

LOAD DATA INFILE '/var/lib/mysql-files/data_csv_init/cities.csv'
INTO TABLE cities
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(city_iata, city_name, fk_country_iso2, city_utc_offset_str, city_utc_offset_min, city_timezone_id);

LOAD DATA INFILE '/var/lib/mysql-files/data_csv_init/airlines.csv'
INTO TABLE airlines
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(airline_iata, airline_icao, airline_name);

LOAD DATA INFILE '/var/lib/mysql-files/data_csv_init/aircrafts.csv'
INTO TABLE aircrafts
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(aircraft_iata, aircraft_icao, aircraft_name, aircraft_wiki_link);

LOAD DATA INFILE '/var/lib/mysql-files/data_csv_init/airports.csv'
INTO TABLE airports
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(airport_iata_code, airport_icao_code, fk_city_iata, fk_country_iso2, airport_name, airport_utc_offset_str, airport_utc_offset_min, airport_timezone_id, airport_latitude, airport_longitude, @airport_wiki_link)
SET airport_wiki_link = IF(CHAR_LENGTH(@airport_wiki_link) > 254, NULL, @airport_wiki_link);

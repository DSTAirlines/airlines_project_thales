CREATE DATABASE Airlines_Static;

USE Airlines_Static;

CREATE TABLE countries(
    country_iso2 VARCHAR(2) NOT NULL PRIMARY KEY,
    country_iso3 VARCHAR(3) DEFAULT NULL,
	country_name VARCHAR(100) NOT NULL,
	country_numeric INT DEFAULT NULL,
	country_wiki_link VARCHAR(255) DEFAULT NULL,
	country_flag VARCHAR(255) DEFAULT NULL
);


CREATE TABLE cities(
	city_iata VARCHAR(3) NOT NULL PRIMARY KEY,
	city_name VARCHAR(100) NOT NULL,
	fk_country_iso2 VARCHAR(2) NOT NULL,
	city_utc_offset_str VARCHAR(20) DEFAULT NULL,
	city_utc_offset_min INT DEFAULT NULL,
	city_timezone_id VARCHAR(100) DEFAULT NULL,
	FOREIGN KEY (fk_country_iso2) REFERENCES countries(country_iso2)
);


CREATE TABLE airlines(
	airline_iata VARCHAR(2) NOT NULL PRIMARY KEY,
	airline_icao VARCHAR(3) DEFAULT NULL,
	airline_name VARCHAR(255) DEFAULT NULL
);


CREATE TABLE aircrafts(
	aircraft_iata VARCHAR(3) NOT NULL PRIMARY KEY,
	aircraft_icao VARCHAR(4) DEFAULT NULL,
	aircraft_name VARCHAR(255) DEFAULT NULL,
	aircraft_wiki_link VARCHAR(255) DEFAULT NULL
);


CREATE TABLE airports(
	airport_iata_code VARCHAR(3) NOT NULL PRIMARY KEY,
	airport_icao_code VARCHAR(4) DEFAULT NULL,
	fk_city_iata VARCHAR(3) NOT NULL,
	fk_country_iso2 VARCHAR(2) NOT NULL,
	airport_name VARCHAR(200) DEFAULT NULL,
	airport_utc_offset_str VARCHAR(20) DEFAULT NULL,
	airport_utc_offset_min INT DEFAULT NULL,
	airport_timezone_id VARCHAR(100) DEFAULT NULL,
	airport_latitude DECIMAL(10, 6) DEFAULT NULL,
	airport_longitude DECIMAL(10, 6) DEFAULT NULL,
	airport_wiki_link VARCHAR(255) DEFAULT NULL,
	FOREIGN KEY (fk_country_iso2) REFERENCES countries(country_iso2),
	FOREIGN KEY (fk_city_iata) REFERENCES cities(city_iata)
);

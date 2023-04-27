-- ---------------------------------
-- CREATE DATABASE
-- ---------------------------------
CREATE DATABASE Airlines_Static
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;
USE Airlines_Static;
SHOW WARNINGS;

-- ----------------------------
-- CREATE TABLE COUNTRIES
-- ----------------------------
CREATE TABLE `countries`  (
  `country_iso2` varchar(2) NOT NULL,
  `country_iso3` varchar(3) DEFAULT NULL,
  `country_name` varchar(100) NOT NULL,
  `country_numeric` int DEFAULT NULL,
  `country_wiki_link` varchar(255) DEFAULT NULL,
  `country_flag` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`country_iso2`)
);
SHOW WARNINGS;

-- ----------------------------
-- CREATE TABLE CITIES
-- ----------------------------
CREATE TABLE `cities`  (
  `city_iata` varchar(3) NOT NULL,
  `city_name` varchar(100) NOT NULL,
  `fk_country_iso2` varchar(2) NOT NULL,
  `city_utc_offset_str` varchar(20) DEFAULT NULL,
  `city_utc_offset_min` int DEFAULT NULL,
  `city_timezone_id` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`city_iata`),
  FOREIGN KEY (`fk_country_iso2`) REFERENCES `countries` (`country_iso2`)
);
SHOW WARNINGS;

-- ----------------------------
-- CREATE TABLE AIRCRAFTS
-- ----------------------------
CREATE TABLE `aircrafts`  (
  `aircraft_iata` varchar(3) NOT NULL,
  `aircraft_icao` varchar(4) DEFAULT NULL,
  `aircraft_name` varchar(255) DEFAULT NULL,
  `aircraft_wiki_link` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`aircraft_iata`)
);
SHOW WARNINGS;

-- ----------------------------
-- CREATE TABLE AIRLINES
-- ----------------------------
CREATE TABLE `airlines`  (
  `airline_iata` varchar(2) NOT NULL,
  `airline_icao` varchar(3) DEFAULT NULL,
  `airline_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`airline_iata`)
);
SHOW WARNINGS;

-- ----------------------------
-- CREATE TABLE AIRPORTS
-- ----------------------------
CREATE TABLE `airports`  (
  `airport_iata` varchar(3) NOT NULL,
  `airport_icao` varchar(4) DEFAULT NULL,
  `fk_city_iata` varchar(3) NOT NULL,
  `airport_name` varchar(200) DEFAULT NULL,
  `airport_utc_offset_str` varchar(20) DEFAULT NULL,
  `airport_utc_offset_min` int DEFAULT NULL,
  `airport_timezone_id` varchar(100) DEFAULT NULL,
  `airport_latitude` decimal(10, 6) DEFAULT NULL,
  `airport_longitude` decimal(10, 6) DEFAULT NULL,
  `airport_wiki_link` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`airport_iata`),
  FOREIGN KEY (`fk_city_iata`) REFERENCES `cities` (`city_iata`)
);
SHOW WARNINGS;

-- ----------------------------
-- CREATE TABLE ROUTES
-- ----------------------------
CREATE TABLE `routes`  (
  `callsign` varchar(10) NOT NULL,
  `fk_airline_iata` varchar(2) DEFAULT NULL,
  `airport_from_time` time DEFAULT NULL,
  `airport_to_time` time DEFAULT NULL,
  `hasStopover` tinyint DEFAULT 0,
  PRIMARY KEY (`callsign`),
  FOREIGN KEY (`fk_airline_iata`) REFERENCES `airlines` (`airline_iata`)
);
SHOW WARNINGS;

-- ----------------------------
-- CREATE TABLE STOPOVERS
-- ----------------------------
CREATE TABLE `stopovers`  (
  `fk_route_callsign` varchar(10) NOT NULL,
  `fk_airport_iata` varchar(3) NOT NULL,
  `escale_total_number` tinyint NOT NULL,
  `escale_order_number` tinyint NOT NULL,
  `no_escale_order` tinyint NOT NULL,
  PRIMARY KEY (`fk_route_callsign`, `fk_airport_iata`),
  FOREIGN KEY (`fk_airport_iata`) REFERENCES `airports` (`airport_iata`),
  FOREIGN KEY (`fk_route_callsign`) REFERENCES `routes` (`callsign`)
);
SHOW WARNINGS;

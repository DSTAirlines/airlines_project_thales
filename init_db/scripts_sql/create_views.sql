USE Airlines_Static;

-- ---------------------------------
-- CREATE VIEW AIRPORT
-- ---------------------------------
CREATE OR REPLACE ALGORITHM = UNDEFINED DEFINER = `airlines-sql-global`@`%` SQL SECURITY DEFINER VIEW `Airlines_Static`.`view_airport` AS SELECT DISTINCT
	`airports`.`airport_iata` AS `airport_iata`,
	`airports`.`airport_icao` AS `airport_icao`,
	`airports`.`fk_city_iata` AS `fk_city_iata`,
	`airports`.`airport_name` AS `airport_name`,
	`airports`.`airport_utc_offset_str` AS `airport_utc_offset_str`,
	`airports`.`airport_utc_offset_min` AS `airport_utc_offset_min`,
	`airports`.`airport_timezone_id` AS `airport_timezone_id`,
	`airports`.`airport_latitude` AS `airport_latitude`,
	`airports`.`airport_longitude` AS `airport_longitude`,
	`airports`.`airport_wiki_link` AS `airport_wiki_link`,
	`cities`.`city_name` AS `city_name`,
	`countries`.`country_name` AS `country_name`,
	`countries`.`country_iso3` AS `country_iso3`,
	`countries`.`country_iso2` AS `country_iso2`,
	`countries`.`country_flag` AS `country_flag`,
	`countries`.`country_wiki_link` AS `country_wiki_link` 
FROM
	((
        `airports`
        LEFT JOIN `cities` ON ((
            `airports`.`fk_city_iata` = `cities`.`city_iata` 
        )))
		LEFT JOIN `countries` ON ((
			`cities`.`fk_country_iso2` = `countries`.`country_iso2` 
	)));

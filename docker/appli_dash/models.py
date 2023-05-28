from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Airline(Base):
    __tablename__ = 'airlines'

    airline_iata = Column(String(2), primary_key=True)
    airline_icao = Column(String(3), nullable=True)
    airline_name = Column(String(255), nullable=True)

class Aircraft(Base):
    __tablename__ = 'aircrafts'
    aircraft_iata = Column(String(3), primary_key=True)
    aircraft_icao = Column(String(4), nullable=True)
    aircraft_name = Column(String(255), nullable=True)
    aircraft_wiki_link = Column(String(255), nullable=True)

class Airport(Base):
    __tablename__ = 'airports'
    airport_iata = Column(String(3), primary_key=True)
    airport_icao = Column(String(4))
    fk_city_iata = Column(String(3), ForeignKey("cities.city_iata"), nullable=False)
    airport_name = Column(String(200), nullable=True)
    airport_utc_offset_str = Column(String(20), nullable=True)
    airport_utc_offset_min = Column(Integer, nullable=True)
    airport_timezone_id = Column(String(100), nullable=True)
    airport_latitude = Column(Float, nullable=True)
    airport_longitude = Column(Float, nullable=True)
    airport_wiki_link = Column(String(255), nullable=True)

class City(Base):
    __tablename__ = 'cities'
    city_iata = Column(String(3), primary_key=True)
    city_name = Column(String(100), nullable=False)
    fk_country_iso2 = Column(String(2), ForeignKey("countries.country_iso2"), nullable=False)
    city_utc_offset_str = Column(String(20), nullable=True)
    city_utc_offset_min = Column(Integer, nullable=True)
    city_timezone_id = Column(String(100), nullable=True)

class Country(Base):
    __tablename__ = 'countries'
    country_iso2 = Column(String(2), primary_key=True)
    country_iso3 = Column(String(3), nullable=True)
    country_name = Column(String(100), nullable=False)
    country_numeric = Column(Integer)
    country_wiki_link = Column(String(255), nullable=True)
    country_flag = Column(String(255), nullable=True)
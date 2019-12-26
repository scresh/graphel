import requests
import csv
from itertools import product

AIRPORTS_URL = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'


class GeoService:
    def __init__(self, airports_url=AIRPORTS_URL):
        self.airports = self._prepare_airports(airports_url)
        self.airports_distances = self._prepare_airports_distances()

    def _prepare_airports(self, database_url: str) -> dict:
        airports = {}
        response = requests.get(database_url).text.strip()
        airports_data = csv.reader(response.split('\n'), delimiter=',', quotechar='"')

        for airport_data in airports_data:
            airport_dict = self._get_airport_dict(airport_data)
            if airport_dict:
                code = airport_dict.pop("code")
                airports[code] = airport_dict

        return airports

    def _prepare_airports_distances(self) -> dict:
        airports_distances = {}
        for code_a, code_b in product(self.airports.keys(), self.airports.keys()):
            latitude_a = self.airports[code_a]['latitude']
            longitude_a = self.airports[code_a]['longitude']

            latitude_b = self.airports[code_b]['latitude']
            longitude_b = self.airports[code_b]['longitude']
            distance = self._get_distance((latitude_a, longitude_a), (latitude_b, longitude_b))

            airports_distances[code_a] = airports_distances.get(code_a, {})
            airports_distances[code_a][code_b] = distance
        return airports_distances

    @staticmethod
    def _get_airport_dict(airport_data: list) -> dict:
        country = airport_data[3]
        code = airport_data[4]
        latitude = round(float(airport_data[6]), 2)
        longitude = round(float(airport_data[7]), 2)

        if len(code) != 3:
            return {}
        else:
            return {"code": code, "country": country, "latitude": latitude, "longitude": longitude}

    @property
    def all_countries(self) -> set:
        return {x["country"] for x in self.airports.values()}

    def get_country(self, airport_code: str) -> str:
        return self.airports.get(airport_code, {}).get("country")

    def get_nearby_airports(self, airport_code: str, max_distance: float) -> list:
        airport_distances = self.airports_distances.get(airport_code, {})
        return [code for code, distance in airport_distances.items() if distance <= max_distance]

    @staticmethod
    def _get_distance(coordinates_a: tuple, coordinates_b: tuple) -> float:
        degree_in_kms = 111.12

        latitude_a, longitude_a = coordinates_a
        latitude_b, longitude_b = coordinates_b

        return degree_in_kms * ((latitude_b - latitude_a)**2 + (longitude_b - longitude_a)**2)**0.5

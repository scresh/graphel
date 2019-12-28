import requests
from csv import DictReader
from itertools import product

AIRPORTS_URL = "https://ourairports.com/data/airports.csv"


class GeoService:
    def __init__(self, airports_url=AIRPORTS_URL):
        response = requests.get(airports_url).text.split("\n")
        airports_csv = DictReader(response, delimiter=',', quotechar='"')
        self.airports = self.get_airports(airports_csv)
        self.distances = self.get_distances(self.airports)

    @classmethod
    def get_airports(cls, airports_csv: DictReader) -> dict:
        airports = {}
        for airport in airports_csv:
            if len(airport['iata_code']) != 3:
                continue

            airports[airport['iata_code']] = {
                "country": airport['iso_country'],
                "latitude": float(airport['latitude_deg']),
                "longitude": float(airport['longitude_deg']),
            }

        return airports

    @classmethod
    def get_distances(cls, airports: dict) -> dict:
        distances = {}
        for code_a, code_b in product(airports.keys(), airports.keys()):
            latitude_a = airports[code_a]['latitude']
            longitude_a = airports[code_a]['longitude']

            latitude_b = airports[code_b]['latitude']
            longitude_b = airports[code_b]['longitude']
            distance = cls.calculate_distance((latitude_a, longitude_a), (latitude_b, longitude_b))

            distances[code_a] = distances.get(code_a, {})
            distances[code_a][code_b] = distance
        return distances

    @classmethod
    def calculate_distance(cls, coordinates_a: tuple, coordinates_b: tuple) -> float:
        degree_in_kms = 111.12

        latitude_a, longitude_a = coordinates_a
        latitude_b, longitude_b = coordinates_b

        latitude_diff = abs(latitude_a - latitude_b)
        longitude_diff = abs(longitude_a - longitude_b)

        shortest_latitude_diff = min(latitude_diff, 360 - latitude_diff)
        shortest_longitude_diff = min(longitude_diff, 360 - longitude_diff)

        return degree_in_kms * (shortest_latitude_diff**2 + shortest_longitude_diff**2)**0.5

    @property
    def countries(self) -> list:
        return list({x["country"] for x in self.airports.values()})

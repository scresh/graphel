import requests
from csv import DictReader
from itertools import product

AIRPORTS_URL = "https://ourairports.com/data/airports.csv"


class GeoService:
    def __init__(self, supported_airports_codes, airports_url=AIRPORTS_URL):
        response = requests.get(airports_url).text.split("\n")
        airports_csv = DictReader(response, delimiter=',', quotechar='"')
        self.airports = self.get_airports(supported_airports_codes, airports_csv)
        self.distances = self.get_distances(self.airports)

    @staticmethod
    def get_airports(supported_airports_codes: list, airports_csv: DictReader) -> list:
        airports = {}

        for airport in airports_csv:
            if (airport['iata_code'] not in supported_airports_codes) or (airport['iata_code'] in airports):
                continue

            airports[airport["iata_code"]] = {
                "country": airport["iso_country"],
                "latitude": round(float(airport['latitude_deg']), 2),
                "longitude": round(float(airport['longitude_deg']), 2),
            }

        return [(k, v["country"], v["latitude"], v["longitude"]) for k, v in airports.items()]

    def get_distances(self, airports: list) -> list:
        distances = []
        for airport_a, airport_b in product(airports, airports):
            coordinates_a = airport_a[3:5]
            coordinates_b = airport_b[3:5]
            distance = self.calculate_distance(coordinates_a, coordinates_b)
            distances.append((airport_a[0], airport_b[0], distance))
        return distances

    @staticmethod
    def calculate_distance(coordinates_a: tuple, coordinates_b: tuple) -> float:
        degree_in_kms = 111.12

        latitude_a, longitude_a = coordinates_a
        latitude_b, longitude_b = coordinates_b

        latitude_diff = abs(latitude_a - latitude_b)
        longitude_diff = abs(longitude_a - longitude_b)

        shortest_latitude_diff = min(latitude_diff, 360 - latitude_diff)
        shortest_longitude_diff = min(longitude_diff, 180 - longitude_diff)

        return round(degree_in_kms * (shortest_latitude_diff**2 + shortest_longitude_diff**2)**0.5, 2)

import requests
import csv

AIRPORTS_URL = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'


class GeolocationService:
    def __init__(self, airports_url=AIRPORTS_URL):
        self.airports = self._prepare_airports(airports_url)

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
    def countries(self) -> set:
        return {x["country"] for x in self.airports.values()}

    def get_country(self, airport_code: str) -> str:
        return self.airports.get(airport_code, {}).get("country")

    def get_nearby_airports(self, airport_code: str, max_distance: float) -> list:
        nearby_airports = []
        airport_origin = self.airports.get(airport_code)

        if not airport_origin:
            return nearby_airports

        latitude_a = airport_origin['latitude']
        longitude_a = airport_origin['longitude']

        for code, airport in self.airports.items():
            latitude_b = airport['latitude']
            longitude_b = airport['longitude']

            distance = self.get_distance((latitude_a, longitude_a), (latitude_b, longitude_b))

            if distance <= max_distance:
                nearby_airports.append(code)

        return nearby_airports

    @staticmethod
    def get_distance(coordinates_a: tuple, coordinates_b: tuple) -> float:
        degree_in_kms = 111.12

        latitude_a, longitude_a = coordinates_a
        latitude_b, longitude_b = coordinates_b

        return degree_in_kms * ((latitude_b - latitude_a)**2 + (longitude_b - longitude_a)**2)**0.5

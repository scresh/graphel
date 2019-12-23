import requests
import csv

AIRPORTS_URL = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'


class GeolocationService:
    def __init__(self, airports_url=AIRPORTS_URL):
        self.airports = self.prepare_airports(airports_url)

    def prepare_airports(self, database_url):
        airports = {}
        response = requests.get(database_url).text.strip()
        airports_data = csv.reader(response.split('\n'), delimiter=',', quotechar='"')

        for airport_data in airports_data:
            airport_dict = self.get_airport_dict(airport_data)
            if airport_dict:
                code = airport_dict.pop("code")
                airports[code] = airport_dict

        return airports

    @staticmethod
    def get_airport_dict(airport_data: list) -> dict:
        country = airport_data[3]
        airport_code = airport_data[4]
        latitude = round(float(airport_data[6]), 2)
        longitude = round(float(airport_data[7]), 2)

        if len(airport_code) != 3:
            return {}
        else:
            return {"code": airport_code, "country": country, "latitude": latitude, "longitude": longitude}

    @property
    def countries(self):
        return {x["country"] for x in self.airports.values()}

    def get(self, airport_code):
        return self.airports.get(airport_code)
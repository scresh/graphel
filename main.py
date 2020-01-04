import peewee

from airlines.wizzair import WizzAir
from tools.geo import GeoService
from tools.database import (
    create_database,
    Country,
    Airport,
    Distance,
    Flight)


class Graphel:
    def __init__(self, db_filename):
        create_database(db_filename)
        self.airlines = (WizzAir(),)
        self.fill_database(
            GeoService(
                self.get_airport_codes(self.airlines)
            )
        )

    @staticmethod
    def get_airport_codes(airlines) -> list:
        airport_codes = []
        for airline in airlines:
            airport_codes.extend(airline.airport_codes)

        return [*set(airport_codes)]

    def fill_database(self, geo_service: GeoService):
        self.fill_countries(geo_service)
        self.fill_airports(geo_service)
        self.fill_distances(geo_service)
        self.fill_flights()

    @staticmethod
    def fill_countries(geo_service):
        Country.insert_many(rows=geo_service.countries, fields=[Country.id, Country.code]).execute()

    @staticmethod
    def fill_airports(geo_service):
        Airport.insert_many(
            rows=geo_service.airports,
            fields=[Airport.id, Airport.code, Airport.country, Airport.latitude, Airport.longitude],
        ).execute()

    @staticmethod
    def fill_distances(geo_service):
        Distance.insert_many(
            rows=geo_service.distances,
            fields=[Distance.source, Distance.destination, Distance.distance],
        ).execute()

    def fill_flights(self):
        for airline in self.airlines:
            for source, destination in airline.connections:
                flight_data = airline.get_flight_data(source, destination, "2020-02-01", "2020-03-01")

                if not flight_data:
                    continue
                length = len(flight_data)

                try:
                    source_ids = [Airport.get(Airport.code == source).id] * length
                    destination_ids = [Airport.get(Airport.code == destination).id] * length
                except peewee.DoesNotExist:
                    continue

                flight_rows = [(x, y) + z for x, y, z in zip(source_ids, destination_ids, flight_data)]
                Flight.insert_many(
                    rows=flight_rows,
                    fields=[Flight.source, Flight.destination, Flight.date, Flight.cost]
                ).execute()


def main():
    graphel = Graphel(':memory:')


if __name__ == '__main__':
    main()

from time import time

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
        self.airlines = (
            WizzAir(),
        )

        self.geo_service = GeoService(self.get_airport_codes())
        self.fill_database()

    def get_airport_codes(self) -> list:
        airport_codes = []
        for airline in self.airlines:
            airport_codes.extend(airline.airport_codes)

        return [*set(airport_codes)]

    def fill_database(self):
        self.fill_countries()
        self.fill_airports()
        self.fill_distances()
        self.fill_flights()

    def fill_countries(self):
        Country.insert_many(
            rows=self.geo_service.countries,
            fields=[Country.id, Country.code]
        ).execute()

    def fill_airports(self):
        Airport.insert_many(
            rows=self.geo_service.airports,
            fields=[Airport.id, Airport.code, Airport.country, Airport.latitude, Airport.longitude],
        ).execute()

    def fill_distances(self):
        Distance.insert_many(
            rows=self.geo_service.distances,
            fields=[Distance.source, Distance.destination, Distance.distance],
        ).execute()

    def fill_flights(self):
        periods = []
        count = 0
        tic = time()

        for airline in self.airlines:
            for source, destination in airline.connections:
                flight_data = airline.get_flight_data(source, destination, "2020-02-01", "2020-03-01")
                tac = time()
                periods.append(tac-tic)
                print(f'{tac-tic}')
                tic = tac
                count += 1
                print(sum(periods) / count)
                print('-' * 100)
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

from airlines.wizzair import WizzAir
from datetime import (
    timedelta,
    datetime,
)
from hashlib import md5
import peewee
from tabulate import tabulate
import tools.database as db
from tools.geo import GeoService

DATABASE_DIR_NAME = "database_files"


class Graphel:
    def __init__(self, date_range, airports_list):
        self.date_start, self.date_stop = date_range
        self.airports_list = tuple(sorted(airports_list))

        self.file_path = self.get_file_path(date_range, self.airports_list)
        db.create_database(self.file_path)
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
        db.insert_airports(self.geo_service.airports)
        db.insert_distances(self.geo_service.distances)
        db.insert_flights(self.get_flights())

    def fill_distances(self):
        db.Distance.insert_many(
            rows=self.geo_service.distances,
            fields=[db.Distance.source, db.Distance.destination, db.Distance.distance],
        ).execute()

    def get_flights(self):
        flights = []

        for airline in self.airlines:
            for source, destination in airline.connections:
                if not all([x in self.airports_list for x in (source, destination)]):
                    continue
                flight_data = airline.get_flight_data(source, destination, self.date_start, self.date_stop)
                if not flight_data:
                    continue
                length = len(flight_data)

                try:
                    source_ids = [db.get_airport_id(source)] * length
                    destination_ids = [db.get_airport_id(destination)] * length
                except peewee.DoesNotExist:
                    continue

                flights.extend([(x, y) + z for x, y, z in zip(source_ids, destination_ids, flight_data)])

        return flights

    def run(self, chain, min_range, max_range, total_cost, recent_airport_and_date=None):
        if recent_airport_and_date:
            recent_airport, recent_date = recent_airport_and_date
        else:
            recent_airport, recent_date = db.get_recent_airport_and_date(chain.id)

        lower_range = self.get_shifted_date_str(recent_date, min_range)
        upper_range = self.get_shifted_date_str(recent_date, max_range)
        amount_left = total_cost - float(chain.cost)

        for flight in db.get_matching_flights(recent_airport, amount_left, lower_range, upper_range):
            new_chain = db.get_new_chain(chain, flight)
            self.run(new_chain, min_range, max_range, total_cost)

    def insert_chains(self, initial_airport, day_range, total_cost):
        min_range, max_range = day_range
        first_chain = db.get_first_chain(initial_airport)
        start_date = self.get_shifted_date_str(self.date_start, -min_range)

        self.run(first_chain, min_range, max_range, total_cost, recent_airport_and_date=(initial_airport, start_date))

    @classmethod
    def get_file_path(cls, date_range, selected_airports):
        filename_base = md5("".join(date_range + selected_airports).encode()).hexdigest()
        file_path = f"{DATABASE_DIR_NAME}/{filename_base}.db"
        return file_path

    @classmethod
    def show_best_results(cls, date_range, initial_airport, airports_to_visit, limit=10, is_one_way=False):
        file_path = cls.get_file_path(date_range, tuple(sorted((initial_airport, ) + airports_to_visit)))
        db.create_database(file_path)

        chains_scores = []

        for chain in db.get_matching_chains(initial_airport, is_one_way):
            chain_flights = db.ChainFlight.select().where(db.ChainFlight.chain_id == chain.id).order_by(
                db.ChainFlight.id)
            visited_airports = [initial_airport]
            visited_countries = {db.get_airport_country(initial_airport)}

            for chain_flight in chain_flights:
                destination = chain_flight.flight.destination.code
                visited_airports.append(destination)
                visited_countries.add(db.get_airport_country(destination))

            chains_scores.append((len(set(visited_airports)), " -> ".join(visited_airports)))

        best_results = sorted(chains_scores, key=lambda x: x[0], reverse=True)[:limit]
        print(tabulate(best_results, headers=["Count", "Route"]))

    @staticmethod
    def get_shifted_date_str(date_str, delta, date_format="%Y-%m-%d"):
        return (datetime.strptime(date_str, date_format) + timedelta(days=delta)).strftime(date_format)

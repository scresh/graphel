from datetime import timedelta, datetime

import peewee
from tabulate import tabulate

from airlines.wizzair import WizzAir
from tools.geo import GeoService
from tools.database import (
    create_database,
    Airport,
    Distance,
    Flight,
    Chain,
    get_matching_flights,
    get_recent_airport_and_date,
    get_new_chain,
    ChainFlight)


class Graphel:
    def __init__(
            self,
            db_filename="airports.db",
            date_range=("2020-02-01", "2020-03-01"),
            selected_airports=(
                    "WAW", "ATH", "VIE", "BRU", "SOF", "LCA", "PGR", "ORY", "SXF",
            ),
    ):
        self.date_start, self.date_stop = date_range
        self.selected_airports = selected_airports

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
        self.fill_airports()
        self.fill_distances()
        self.fill_flights()

    def fill_airports(self):
        Airport.insert_many(
            rows=self.geo_service.airports,
            fields=[Airport.code, Airport.country, Airport.latitude, Airport.longitude],
        ).execute()

    def fill_distances(self):
        Distance.insert_many(
            rows=self.geo_service.distances,
            fields=[Distance.source, Distance.destination, Distance.distance],
        ).execute()

    def fill_flights(self):
        for airline in self.airlines:
            for source, destination in airline.connections:
                if not all([x in self.selected_airports for x in (source, destination)]):
                    continue
                flight_data = airline.get_flight_data(source, destination, self.date_start, self.date_stop)
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

    def run(self, chain, min_range, max_range, total_cost, recent_airport_and_date=None):
        if recent_airport_and_date:
            recent_airport, recent_date = recent_airport_and_date
        else:
            recent_airport, recent_date = get_recent_airport_and_date(chain.id)

        lower_range = get_date_str_after_delta(recent_date, min_range)
        upper_range = get_date_str_after_delta(recent_date, max_range)
        amount_left = total_cost - chain.cost

        for flight in get_matching_flights(recent_airport, amount_left, lower_range, upper_range):
            new_chain = get_new_chain(chain, flight)
            self.run(new_chain, min_range, max_range, total_cost)

    def insert_chains(self, start_airport="WAW", min_range=2, max_range=4, total_cost=120):
        genesis_chain = Chain.get(Chain.id == Chain.insert(cost=0).execute())
        start_date = get_date_str_after_delta(self.date_start, -min_range)

        self.run(genesis_chain, min_range, max_range, total_cost, recent_airport_and_date=(start_airport, start_date))

    @classmethod
    def show_best_results(cls, limit=10):
        create_database('airports.db')

        chain_n_score = []

        for chain in Chain.select():
            chain_flights = ChainFlight.select().where(ChainFlight.chain_id == chain.id).order_by(ChainFlight.id)
            visited_airports = set()
            airports_pairs = []

            for chain_flight in chain_flights:
                source = chain_flight.flight.source.code
                destination = chain_flight.flight.destination.code
                [visited_airports.add(x) for x in (source, destination)]
                airports_pairs.append(f"({source} -> {destination})")

            chain_n_score.append((len(visited_airports), "-".join(airports_pairs)))

        best_results = sorted(chain_n_score, key=lambda x: x[0], reverse=True)[:limit]
        print(tabulate(best_results, headers=["Count", "Route"]))


def main():
    graphel = Graphel()
    graphel.insert_chains()
    Graphel.show_best_results()


def get_date_str_after_delta(date_str, delta, date_format="%Y-%m-%d"):
    return (datetime.strptime(date_str, date_format) + timedelta(days=delta)).strftime(date_format)


if __name__ == "__main__":
    main()

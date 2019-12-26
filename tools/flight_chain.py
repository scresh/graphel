from tools.geolocation import GeoService
from copy import deepcopy


class FlightChain:
    def __init__(self, start_airport, start_index, geo_service=None):
        self.connections = list()
        self.dates = list()
        self.prices = list()

        self.countries = set()
        self.current_airport = start_airport
        self.current_index = -start_index
        self.current_cost = 0

        self.geo_service = geo_service if geo_service else GeoService()

    def add(self, flight) -> None:
        source, destination, index, price = flight
        self.connections.append((source, destination))
        self.dates.append(index)
        self.prices.append(price)

        self.countries.add(self.geo_service.get_country(source))
        self.countries.add(self.geo_service.get_country(destination))
        self.current_airport = destination
        self.current_index = index
        self.current_cost += price

    def get_nearby_airports(self, distance):
        if distance:
            return self.geo_service.get_nearby_airports(self.current_airport, distance)
        else:
            return [self.current_airport]

    @property
    def value(self):
        return {
            'connections': self.connections,
            'dates': self.dates,
            'prices': self.prices,
            'countries': self.countries,
        }

    @property
    def clone(self):
        clone = FlightChain(self.current_airport, self.current_index, geo_service=self.geo_service)
        clone.connections = deepcopy(self.connections)
        clone.dates = deepcopy(self.dates)
        clone.countries = deepcopy(self.countries)
        clone.prices = deepcopy(self.prices)
        clone.current_cost = self.current_cost
        return clone

import json
from copy import deepcopy


class FlightChain(list):
    def __init__(self, source, amount, index_range):
        self.current_source = source
        self.amount_left = amount
        self.recent_index = 0
        self.index_range = index_range

        super().__init__()

    def add(self, flight) -> None:
        src, dst, idx, price = flight
        if src != self.current_source:
            raise ValueError('Incorrect source airport')

        if not (self.recent_index + self.index_range[0] <= idx <= self.recent_index + self.index_range[1]):
            raise ValueError('Incorrect idx')

        if price > self.amount_left:
            raise ValueError('Price too high')

        super().append(flight)
        self.amount_left -= price
        self.recent_index = idx
        self.current_source = dst

    @property
    def get_value(self):
        return " --> ".join([str(x) for x in self])


def find_flights(fc_parent, data, results):
    current_source = fc_parent.current_source
    start_index = fc_parent.recent_index + fc_parent.index_range[0]
    stop_index = fc_parent.recent_index + fc_parent.index_range[1]
    amount_left = fc_parent.amount_left

    matching_flights = deepcopy(data[current_source][start_index:stop_index])
    for i in range(len(matching_flights)):
        matching_flights[i] = [*filter(lambda x: x[1] <= amount_left, matching_flights[i])]

    if not any(matching_flights):
        open('results.txt', 'a+').write(f'{fc_parent.get_value}\n')
    else:
        for i in range(len(matching_flights)):
            for flight in matching_flights[i]:
                fc_child = deepcopy(fc_parent)
                src = fc_child.current_source
                dst = flight[0]
                idx = fc_child.recent_index + fc_child.index_range[0] + i
                price = flight[1]
                fc_child.add((src, dst, idx, price))
                find_flights(fc_child, data, results)


def main():
    data = json.loads(open('data.txt').read())
    results = []
    fc = FlightChain('WAW', 100.0, (2, 4))

    find_flights(fc, data, results)

    for x in results:
        print(x)


if __name__ == '__main__':
    main()

from graphel import Graphel


def main():
    initial_airport = "WAW"
    airports_to_visit = ("ATH", "VIE", "BRU", "SOF", "LCA", "PGR", "ORY", "SXF")
    date_range = ("2020-02-01", "2020-03-01")
    day_range = (2, 4)
    total_cost = 120.0

    graphel = Graphel(date_range, (initial_airport, ) + airports_to_visit)
    graphel.insert_chains(initial_airport, day_range, total_cost)

    Graphel.show_best_results(date_range, initial_airport, airports_to_visit, )


if __name__ == "__main__":
    main()

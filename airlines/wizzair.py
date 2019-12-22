from requests import Session
from tools.exchange import ExchangeService


class WizzAirApi:
    def __init__(self, language_code='en-gb', wizzair_domain='wizzair.com'):
        self.language_code = language_code
        self.wizzair_domain = wizzair_domain

        self.es = ExchangeService()
        self.session = Session()
        self.session.headers.update(self.default_headers)
        self.session.get(f'https://{wizzair_domain}/#/')

        self.api_url = f'https://be.{self.wizzair_domain}/{self.api_version}/Api'

    @property
    def default_headers(self):
        return {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/78.0.3904.108 Safari/537.36',
            'accept-encoding': 'gzip, deflate, br',
        }

    @property
    def post_headers(self):
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.5',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': f'https://{self.wizzair_domain}',
            'pragma': 'no-cache',
            'referer': f'https://{self.wizzair_domain}/',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'x-requestverificationtoken': self.session.cookies.get('RequestVerificationToken'),
        }

    @property
    def api_version(self):
        response = self.session.get(f'https://{self.wizzair_domain}/buildnumber').text
        try:
            api_version = response.split()[2].split('/')[-1]
        except IndexError:
            raise ValueError('Incorrect format of /buildnumber response')
        return api_version

    @property
    def city_map(self):
        response = self.session.get(f'{self.api_url}/asset/map?languageCode={self.language_code}').json()
        city_map = {}

        for city in response['cities']:
            city_name = city['iata']
            city_connections = [c['iata'] for c in city['connections']]
            city_map[city_name] = city_connections

        return city_map

    @property
    def pairs(self):
        pairs = set()
        for departure_station, arrival_stations in self.city_map.items():
            for arrival_station in arrival_stations:
                pair = tuple(sorted([departure_station, arrival_station]))
                pairs.add(pair)

        return list(pairs)

    def get_flight_dates(self, src, dst, start, stop):
        response = self.session.get(
            f'{self.api_url}/search/flightDates',
            params={
                'departureStation': src,
                'arrivalStation': dst,
                'from': start,
                'to': stop,
            },
        ).json()

        flight_dates = [fd[:10] for fd in response['flightDates']]
        return flight_dates

    def get_timetable(self, src, dst, start, stop):
        response = self.session.post(
            url=f'{self.api_url}/search/timetable',
            json={
                "flightList": [
                    {"departureStation": src, "arrivalStation": dst, "from": start, "to": stop},
                    {"departureStation": dst, "arrivalStation": src, "from": start, "to": stop},
                ],
                "priceType": "regular",
                "adultCount": 1,
                "childCount": 0,
                "infantCount": 0,
            },
            headers=self.post_headers,
        ).json()

        flights = {src: {}, dst: {}}
        self.insert_flights(response, flights)

        return flights

    def insert_flights(self, response, flights):
        for flight in response['outboundFlights'] + response['returnFlights']:
            date = flight['departureDate'][:10]
            src = flight['departureStation']
            dst = flight['arrivalStation']
            price = flight['price']['amount']
            currency = flight['price']['currencyCode']

            eur_price = self.es.get_eur_price(price, currency)

            if src not in flights:
                break

            flights[src][date] = flights[src].get(date, []) + [(dst, eur_price)]

        return flights

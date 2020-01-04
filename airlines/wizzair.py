from requests import Session
from tools.exchange import ExchangeService


class WizzAir:
    def __init__(self, wizzair_domain='wizzair.com'):
        self.wizzair_domain = wizzair_domain

        self.es = ExchangeService()
        self.session = Session()
        self.session.headers.update(self.default_headers)
        self.session.get(f'https://{wizzair_domain}/#/')

        self.api_url = f'https://be.{self.wizzair_domain}/{self.api_version}/Api'
        self.airport_codes, self.connections = self.get_airport_codes_and_connections()

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

    def get_airport_codes_and_connections(self) -> tuple:
        response = self.session.get(f'{self.api_url}/asset/map?languageCode=en-gb').json()
        airport_codes, connections = [[] for _ in range(2)]

        for city in response['cities']:
            city_name = city['iata']
            city_connections = [c['iata'] for c in city['connections']]
            length = len(city_connections)
            connections.extend([*zip([city_name] * length, city_connections)])
            airport_codes.append(city_name)

        return airport_codes, connections

    def get_flight_data(self, source: str, destination: str, start: str, stop: str) -> list:
        response = self.session.post(
            url=f'{self.api_url}/search/timetable',
            json={
                "flightList": [
                    {"departureStation": source, "arrivalStation": destination, "from": start, "to": stop},
                    {"departureStation": destination, "arrivalStation": source, "from": start, "to": stop},
                ],
                "priceType": "regular",
                "adultCount": 1,
                "childCount": 0,
                "infantCount": 0,
            },
            headers=self.post_headers,
        ).json()

        pair = sorted((source, destination))
        return self.fetch_flight_data(response, pair)

    def fetch_flight_data(self, response: dict, airport_pair: list) -> list:
        flight_data = []
        for flight in response['outboundFlights'] + response['returnFlights']:
            if sorted((flight['departureStation'], flight['arrivalStation'])) != airport_pair:
                break

            date = flight['departureDate'][:10]
            price = flight['price']['amount']
            currency = flight['price']['currencyCode']
            eur_price = self.es.get_eur_price(price, currency)
            if eur_price == 0.0:
                continue

            flight_data.append((date, eur_price))

        return flight_data

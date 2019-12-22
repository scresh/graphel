import requests


class ExchangeService:
    def __init__(self):
        self.rate_dict = {'PLN': 1.0}

        for table_code in ('a', 'b'):
            self.insert_table_rates(table_code)

        self.convert_rates_to_eur()

    def insert_table_rates(self, table_code):
        rates = requests.get(
            f'http://api.nbp.pl/api/exchangerates/tables/{table_code}',
            params={'format': 'json'},
        ).json()[0]['rates']

        for rate in rates:
            code = rate['code']
            price = rate['mid']
            self.rate_dict[code] = price

    def convert_rates_to_eur(self):
        eur_rate = self.rate_dict['EUR']

        for code, price in self.rate_dict.items():
            self.rate_dict[code] = price / eur_rate

    def get_eur_price(self, amount, currency):
        rate = self.rate_dict[currency]
        return round(amount * rate, 2)

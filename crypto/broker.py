import requests
from enum import Enum
from collections import defaultdict

from crypto.constants import Currency


class Operation(Enum):
    BUY = 'BUY'
    SELL = 'SELL'


class PriceType(Enum):
    BID = 'BID'
    ASK = 'ASK'


class ExchangeRate:
    def __init__(self, price_type, src, dst, rate):
        self.price_type = price_type
        self.from_currency = src
        self.to_currency = dst
        self.rate = rate

    def __str__(self):
        return f'[{self.price_type.value}] 1 {self.from_currency.value} ~ {self.to_currency.value} {self.rate}'


class Broker:
    name = 'N/A'
    api_url = 'N/A'
    available_pairs = {}
    buy_fees = {}
    sell_fees = {}

    def __init__(self, commission=0.0):
        self.commission = commission
        self._exchange_rates = defaultdict(list)

    @classmethod
    def create(cls, name):
        return next(subclass() for subclass in cls.__subclasses__() if subclass.name == name)

    def get_pair(self, src_currency, dst_currency):
        if (src_currency, dst_currency) in self.available_pairs:
            return src_currency, dst_currency
        elif (dst_currency, src_currency) in self.available_pairs:
            return dst_currency, src_currency
        else:
            raise ValueError

    def sync_exchange_rate(self, src_currency, dst_currency):
        raise NotImplementedError

    def sell_to_receive(self, amount, of_currency, for_currency):
        """Sell {return_value} to broker to receive {amount}"""

        exchange_rate = self.exchange_rate(PriceType.BID, of_currency, for_currency).rate

        pair = self.get_pair(of_currency, for_currency)
        fee = self.buy_fees.get(for_currency, 0.00)

        if (of_currency, for_currency) == pair:
            amount_to_sell = amount * exchange_rate
        else:
            amount_to_sell = amount / exchange_rate

        amount_to_sell = (amount_to_sell * (1.0 + self.commission)) + fee

        return amount_to_sell

    def buy(self, amount, of_currency, for_currency):
        """ Buy {amount} from broker to receive {return_value} """

        exchange_rate = self.exchange_rate(PriceType.ASK, of_currency, for_currency).rate

        pair = self.get_pair(of_currency, for_currency)
        fee = self.sell_fees.get(of_currency, 0.00)

        if (of_currency, for_currency) == pair:
            amount_to_pay = (amount + fee) * exchange_rate
        else:
            amount_to_pay = (amount + fee) / exchange_rate

        amount_to_pay = amount_to_pay * (1.0 + self.commission)

        return amount_to_pay

    def add_exchange_rate(self, pair, rate):
        """
        Add the exchange rate to the list of BUY and SELL operations.

        :param rate: The rate in the form of an ExchangeRate object.
        :param operation: The BUY or SELL operation from the perspective of the broker. For example: If
            the operation is BUY going from BTC to EUR, the broker buys my BTC in exchange for EUR. If the operation is
            SELL from BTC to EUR, the broker sells me BTC in exchange for EUR.
        """
        self._exchange_rates[pair].append(rate)

    def exchange_rate(self, price_type, from_currency, to_currency):
        pair = self.get_pair(src_currency=from_currency, dst_currency=to_currency)
        exchange_rate = next(rate for rate in self._exchange_rates[pair] if rate.price_type == price_type)

        return exchange_rate


class RipioBroker(Broker):
    name = 'Ripio'
    api_url = 'https://app.ripio.com/api/v3/public/rates/?country=AR'
    available_pairs = {
        (Currency.BTC, Currency.ARS),
        (Currency.DAI, Currency.ARS),
    }

    def __init__(self):
        super(RipioBroker, self).__init__(commission=0.01)

    def sync_exchange_rate(self, src_currency, dst_currency):
        pair = self.get_pair(src_currency, dst_currency)
        key = '_'.join(c.value for c in pair)

        exchange_rate_data = requests.get(self.api_url).json()
        exchange_rate = next(rate for rate in exchange_rate_data if rate['ticker'] == key)

        self.add_exchange_rate(pair, ExchangeRate(PriceType.ASK, *pair, float(exchange_rate['buy_rate'])))   # noqa
        self.add_exchange_rate(pair, ExchangeRate(PriceType.BID, *pair, float(exchange_rate['sell_rate'])))  # noqa


class SatoshiTangoBroker(Broker):
    name = 'satoshi_tango'

    def __init__(self):
        super(SatoshiTangoBroker, self).__init__(url='https://api.satoshitango.com/v2/ticker')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url).json()
        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(exchange_rate_data['data']['compra']['arsbtc'])))


class BuenBitBroker(Broker):
    name = 'buenbit'

    def __init__(self):
        super(BuenBitBroker, self).__init__(url='https://customers.buenbit.com/api/v1/market/tickers')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url).json()
        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(exchange_rate_data['object']['btcars']['selling_price'])))


class LetsBit(Broker):
    name = 'Let\'s Bit'
    api_url = 'https://letsbit.io/api/v1/exchange/public/markets/tickers'
    available_pairs = {
        (Currency.BTC, Currency.ARS),
        (Currency.DAI, Currency.ARS),
    }
    buy_fees = {
        Currency.BTC: 0.0002,
        Currency.DAI: 10.0,
    }
    sell_fees = {
        Currency.BTC: 0.0002,
        Currency.DAI: 10.0,
    }

    def sync_exchange_rate(self, src_currency, dst_currency):
        pair = self.get_pair(src_currency, dst_currency)
        key = ''.join(c.value for c in pair).lower()

        exchange_rate_data = requests.get(self.api_url).json()
        exchange_rate = exchange_rate_data[key]['ticker']

        self.add_exchange_rate(pair, ExchangeRate(PriceType.ASK, *pair, float(exchange_rate['sell'])))
        self.add_exchange_rate(pair, ExchangeRate(PriceType.BID, *pair, float(exchange_rate['buy'])))


class BitsoBroker(Broker):
    name = 'bitso'

    def __init__(self):
        super(BitsoBroker, self).__init__(url='https://api.bitso.com/v3/ticker/')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url).json()
        btc_ars_rate = next(rate for rate in exchange_rate_data['payload'] if rate['book'] == 'btc_ars')

        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(btc_ars_rate['ask'])))


class BitexBroker(Broker):
    name = 'bitex'

    def __init__(self):
        super(BitexBroker, self).__init__(url='https://bitex.la/api/tickers')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url).json()
        btc_ars_rate = next(rate for rate in exchange_rate_data['data'] if rate['id'] == 'btc_ars')

        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(btc_ars_rate['attributes']['ask'])))


class ArgenBTCBroker(Broker):
    name = 'argenbtc'

    def __init__(self):
        super(ArgenBTCBroker, self).__init__(url='https://argenbtc.com/public/cotizacion_js.php')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url).json()
        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(exchange_rate_data['precio_compra'])))


class BudaBroker(Broker):
    name = 'buda'

    def __init__(self):
        super(BudaBroker, self).__init__(url='https://www.buda.com/api/v2/markets')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url + '/btc-ars/ticker').json()
        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(exchange_rate_data['ticker']['last_price'][0])))


class CryptomarketBroker(Broker):
    name = 'cryptomarket'

    def __init__(self):
        super(CryptomarketBroker, self).__init__(url='https://api.cryptomkt.com/v1/ticker')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url).json()
        btc_ars_rate = next(rate for rate in exchange_rate_data['data'] if rate['market'] == 'BTCARS')

        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(btc_ars_rate['ask'])))


class iBitt(Broker):
    name = 'ibitt'

    def __init__(self):
        super(iBitt, self).__init__(url='https://api.ibitt.co/v2/public/marketSummaries')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url + '/BTC-ARS').json()
        self.add_exchange_rate(Operation.SELL, ExchangeRate(currency, Currency.ARS,
                                                            float(exchange_rate_data['ask'])))


class BitonicBroker(Broker):
    name = 'bitonic'

    def __init__(self):
        super(BitonicBroker, self).__init__(url='https://bitonic.nl/api/buy')

    def sync_exchange_rates(self, currency):
        exchange_rate_data = requests.get(self.url).json()
        self.add_exchange_rate(Operation.BUY, ExchangeRate(currency, Currency.EUR,
                                                           float(exchange_rate_data['price'])))


class BitvavoBroker(Broker):
    name = 'Bitvavo'
    api_url = 'https://api.bitvavo.com/v2/ticker/book'
    available_pairs = [
        (Currency.BTC, Currency.EUR),
        (Currency.DAI, Currency.EUR),
    ]
    buy_fees = {
        Currency.BTC: 0.0003,
    }

    def sync_exchange_rate(self, src_currency, dst_currency):
        pair = self.get_pair(src_currency, dst_currency)
        key = '-'.join(c.value for c in pair)

        exchange_rate_data = requests.get(self.api_url).json()
        exchange_rate = next(rate for rate in exchange_rate_data if rate['market'] == key)

        self.add_exchange_rate(pair, ExchangeRate(PriceType.ASK, *pair, float(exchange_rate['ask'])))   # noqa
        self.add_exchange_rate(pair, ExchangeRate(PriceType.BID, *pair, float(exchange_rate['bid'])))   # noqa

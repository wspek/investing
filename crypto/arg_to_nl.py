import requests
from collections import defaultdict
from enum import Enum

EUR_TO_RECEIVE = 257.59
SATOSHI = 0.00000001


class Operation(Enum):
    BUY = 'buy'
    SELL = 'sell'


class Currency(Enum):
    ARS = 'ARS'
    EUR = 'EUR'
    USD = 'USD'
    BTC = 'BTC'


class Brokers(Enum):
    RIPIO = 'ripio'
    BITONIC = 'bitonic'


class ExchangeRate:
    def __init__(self, src, dst, rate):
        self.from_currency = src
        self.to_currency = dst
        self.rate = rate

    def __str__(self):
        return '1 {} ~ {} {}'.format(self.from_currency.value, self.rate, self.to_currency.value)


class Broker:
    name = 'baseclass'

    def __init__(self, url, commission=0.00):
        self.url = url
        self.commission = commission
        self._exchange_rates = defaultdict(list)

        self.sync_exchange_rates()

    @classmethod
    def create(cls, name):
        return next(subclass() for subclass in cls.__subclasses__() if subclass.name == name)

    def sync_exchange_rates(self):
        pass

    def buy(self, amount, currency, with_currency):
        """
        Buy operation from the perspective of a broker (buying from a client). Buying {amount} of {currency}
        from customer {with_currency}.

        :param amount: The amount of currency to be bought.
        :param currency: The currency to be bought from the customer.
        :param with_currency: The currency to be delivered to the customer.
        :return: The amount of destination currency (with_currency) delivered.
        """

        exchange_rate = self.exchange_rate(Operation.BUY, currency, with_currency).rate * (1.0 - self.commission)
        to_deliver = amount * exchange_rate

        return to_deliver

    def sell(self, amount, currency, for_currency):
        """
        Sell operation from the perspective of a broker (selling to the client). Selling {amount} of {currency}
        to customer {for_currency}.

        :param amount: The amount of currency to be sold.
        :param currency: The currency to be sold to the customer.
        :param for_currency: The currency to be paid by the customer.
        :return: The cost of the transaction (in for_currency) to be paid by the customer.
        """

        exchange_rate = self.exchange_rate(Operation.SELL, currency, for_currency).rate * (1.0 + self.commission)
        to_pay = amount * exchange_rate

        return to_pay

    def add_exchange_rate(self, operation, rate):
        """
        Add the exchange rate to the list of BUY and SELL operations.

        :param rate: The rate in the form of an ExchangeRate object.
        :param operation: The BUY or SELL operation from the perspective of the broker. For example: If
            the operation is BUY going from BTC to EUR, the broker buys my BTC in exchange for EUR. If the operation is
            SELL from BTC to EUR, the broker sells me BTC in exchange for EUR.
        """
        self._exchange_rates[operation].append(rate)

    def exchange_rate(self, operation, from_currency, to_currency):
        rates = self._exchange_rates[operation]

        exchange_rate = next(exchange_rate for exchange_rate in rates
                             if exchange_rate.from_currency == from_currency
                             and exchange_rate.to_currency == to_currency)

        return exchange_rate


class RipioBroker(Broker):
    name = 'ripio'

    def __init__(self):
        super(RipioBroker, self).__init__(url='https://api.exchange.ripio.com/api/v1/rate/BTC_ARS/', commission=0.01)

    def sync_exchange_rates(self):
        exchange_rate_data = requests.get(self.url).json()
        self.add_exchange_rate(Operation.SELL, ExchangeRate(Currency.BTC, Currency.ARS, float(exchange_rate_data['ask'])))


class BitonicBroker(Broker):
    name = 'bitonic'

    def __init__(self):
        super(BitonicBroker, self).__init__(url='https://bitonic.nl/api/sell')

    def sync_exchange_rates(self):
        exchange_rate_data = requests.get(self.url).json()
        self.add_exchange_rate(Operation.BUY, ExchangeRate(Currency.BTC, Currency.EUR, float(exchange_rate_data['price'])))


class BitcoinAgent:
    fee_url = 'https://api.blockchain.info/mempool/fees'

    @staticmethod
    def fee(inputs=1, outputs=2, priority=True):
        transaction_size_bytes = (inputs * 148) + (outputs * 34) + 10 + inputs

        fees = requests.get('https://api.blockchain.info/mempool/fees').json()
        fee_in_satoshis = fees['priority'] if priority else fees['regular']

        return fee_in_satoshis * transaction_size_bytes


class Client:
    def send_amount(self, pesos, broker_arg=Brokers.RIPIO, broker_nl=Brokers.BITONIC):
        src_broker = Broker.create(name=broker_arg.value)
        dst_broker = Broker.create(name=broker_nl.value)

        # First buy BTC in Argentina
        cost_ars = src_broker.sell(1.0, currency=Currency.BTC, for_currency=Currency.ARS)
        amount_of_btc = pesos / cost_ars

        # Calculate the amount to receive after fee
        fee = BitcoinAgent.fee()
        amount_of_btc_after_fee = amount_of_btc - (fee * SATOSHI)

        # Then sell in Holland
        receive_eur = dst_broker.buy(amount=amount_of_btc_after_fee, currency=Currency.BTC, with_currency=Currency.EUR)

        return {'EUR': round(receive_eur, 2), 'BTC': round(amount_of_btc, 8),
                'fee_satoshi': fee, 'fee_ars': round(fee * SATOSHI * cost_ars, 2)}

    def receive_amount(self, euros, broker_arg=Brokers.RIPIO, broker_nl=Brokers.BITONIC):
        src_broker = Broker.create(name=broker_arg.value)
        dst_broker = Broker.create(name=broker_nl.value)

        # BTC to pay in NL
        eur_per_btc = dst_broker.buy(amount=1.0, currency=Currency.BTC, with_currency=Currency.EUR)
        amount_of_btc = euros / eur_per_btc

        # Calculate amount to send including fee
        fee = BitcoinAgent.fee()
        amount_of_btc += fee * SATOSHI

        # Cost in ARG
        cost_ars = src_broker.sell(amount_of_btc, currency=Currency.BTC, for_currency=Currency.ARS)

        return {'ARS': round(cost_ars, 2), 'BTC': round(amount_of_btc, 8),
                'fee_satoshi': fee, 'fee_eur': round(fee * SATOSHI * eur_per_btc, 2)}


if __name__ == '__main__':
    client = Client()

    cost_in_ars = client.receive_amount(euros=EUR_TO_RECEIVE)
    print('{} ARS > {} BTC > {} EUR'.format(cost_in_ars['ARS'], cost_in_ars['BTC'], EUR_TO_RECEIVE))
    print(cost_in_ars)

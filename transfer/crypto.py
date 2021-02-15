import requests
from enum import Enum

from transfer.oracle import EthereumOracle, BitcoinOracle
from transfer.institution import Institution, Currency


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


class CryptoWallet(Institution):
    api_url = ''

    def __init__(self, name):
        super().__init__(name)

    def get_transfer_fee(self, dst_currency):
        if dst_currency in (Currency.ETH, Currency.DAI, Currency.USDT):
            return EthereumOracle.fee(dst_currency)
        elif dst_currency == Currency.BTC:
            return BitcoinOracle.fee()
        else:
            return 0.0

    def execute_transfer(self, transfer):
        fee = self.get_transfer_fee(transfer.dst_account.currency)

        if transfer.reverse:
            amount = transfer.amount + fee
            transfer.dst_account.withdraw(transfer.amount)
            transfer.src_account.deposit(amount)
        else:
            amount = transfer.amount - fee
            transfer.src_account.withdraw(transfer.amount)
            transfer.dst_account.deposit(amount)

        return amount


class CryptoExchange(CryptoWallet):
    commission = 0.0

    def bid_price(self, src_currency, dst_currency):
        raise NotImplementedError

    def ask_price(self, src_currency, dst_currency):
        raise NotImplementedError

    def get_online_rates(self):
        response = requests.get(self.api_url)
        return response.json()

    def execute_exchange(self, exchange):
        src_currency = exchange.src_account.currency
        dst_currency = exchange.dst_account.currency

        # Buy
        if self.is_crypto(dst_currency):
            ask_price = self.ask_price(src_currency, dst_currency)

            if exchange.reverse:
                src_amount = (exchange.amount * ask_price) / (1.0 - self.commission)
                exchange.dst_account.withdraw(exchange.amount)
                exchange.src_account.deposit(src_amount)
                return src_amount
            else:
                dst_amount = (exchange.amount * (1.0 - self.commission)) / ask_price
                exchange.src_account.withdraw(exchange.amount)
                exchange.dst_account.deposit(dst_amount)
                return dst_amount

        # Sell
        elif self.is_crypto(src_currency):
            bid_price = self.bid_price(src_currency, dst_currency)

            if exchange.reverse:
                src_amount = exchange.amount / (bid_price - (bid_price * self.commission))
                exchange.dst_account.withdraw(exchange.amount)
                exchange.src_account.deposit(src_amount)
                return src_amount
            else:
                dst_amount = (exchange.amount * bid_price) * (1.0 - self.commission)
                exchange.src_account.withdraw(exchange.amount)
                exchange.dst_account.deposit(dst_amount)
                return dst_amount


class RipioExchange(CryptoExchange):
    api_url = 'https://app.ripio.com/api/v3/public/rates/?country=AR'
    commission = 0.01
    available_pairs = [
        (Currency.BTC, Currency.ARS),
        (Currency.DAI, Currency.ARS),
    ]

    def __init__(self):
        super(RipioExchange, self).__init__(name='Ripio')

    def rates(self, src_currency, dst_currency):
        exchange_rates = self.get_online_rates()
        src, dst = self.get_pair(src_currency, dst_currency)
        return next(rate for rate in exchange_rates if rate['ticker'] == f'{src.value}_{dst.value}')

    def bid_price(self, src_currency, dst_currency):
        return float(self.rates(src_currency, dst_currency)['sell_rate'])

    def ask_price(self, src_currency, dst_currency):
        return float(self.rates(src_currency, dst_currency)['buy_rate'])


class LetsBitExchange(CryptoExchange):
    api_url = 'https://letsbit.io/api/v1/exchange/public/markets/tickers'
    dai_withdrawal_fee = 5.0
    btc_withdrawal_fee = 0.00025
    usdt_withdrawal_fee = 5.0
    pax_withdrawal_fee = 5.0
    available_pairs = [
        (Currency.BTC, Currency.ARS),
        (Currency.DAI, Currency.ARS),
        (Currency.USDT, Currency.ARS),
        (Currency.PAX, Currency.ARS),
    ]

    def __init__(self):
        super(LetsBitExchange, self).__init__(name='LetsBit')

    def rates(self, src_currency, dst_currency):
        exchange_rates = super(LetsBitExchange, self).get_online_rates()
        src, dst = self.get_pair(src_currency, dst_currency)
        return next(rate['ticker'] for key, rate in exchange_rates.items() if key == f'{src.value}{dst.value}'.lower())

    def bid_price(self, src_currency, dst_currency):
        return float(self.rates(src_currency, dst_currency)['buy'])

    def ask_price(self, src_currency, dst_currency):
        return float(self.rates(src_currency, dst_currency)['sell'])

    def get_transfer_fee(self, currency):
        # It seems the network fee is already incorporated in the fee that Let's Bit charges.
        # fee = super(LetsBitExchange, self).get_transfer_fee(currency)

        if currency == Currency.DAI:
            return self.dai_withdrawal_fee
        elif currency == Currency.BTC:
            return self.btc_withdrawal_fee
        elif currency == Currency.USDT:
            return self.usdt_withdrawal_fee
        elif currency == Currency.PAX:
            return self.pax_withdrawal_fee


class BitvavoExchange(CryptoExchange):
    api_url = 'https://api.bitvavo.com/v2/ticker/book'
    commission = 0.0025
    available_pairs = {
        (Currency.BTC, Currency.EUR),
        (Currency.DAI, Currency.EUR),
        (Currency.USDT, Currency.EUR),
        # (Currency.PAX, Currency.EUR),     # Does not seem available
    }

    def __init__(self):
        super(BitvavoExchange, self).__init__(name='Bitvavo')

    def rates(self, src_currency, dst_currency):
        exchange_rates = self.get_online_rates()
        src, dst = self.get_pair(src_currency, dst_currency)
        return next(rate for rate in exchange_rates if rate['market'] == f'{src.value}-{dst.value}')

    def bid_price(self, src_currency, dst_currency):
        return float(self.rates(src_currency, dst_currency)['bid'])

    def ask_price(self, src_currency, dst_currency):
        return float(self.rates(src_currency, dst_currency)['ask'])


class BinanceExchange(CryptoExchange):
    api_url = 'https://www.binance.com/api/v3/ticker/price'
    commission = 0.005
    available_pairs = {
        (Currency.BTC, Currency.EUR),
        (Currency.EUR, Currency.USDT),
        # (Currency.EUR, Currency.PAX),     # Does not seem available
        (Currency.DAI, Currency.USDT),
    }

    def __init__(self):
        super(BinanceExchange, self).__init__(name='Binance')

    def rates(self, src_currency, dst_currency):
        exchange_rates = self.get_online_rates()

        try:
            rate = next(rate for rate in exchange_rates if rate['symbol'] == f'{src_currency.value}{dst_currency.value}')   # noqa
            return float(rate['price'])
        except StopIteration:
            rate = next(rate for rate in exchange_rates if rate['symbol'] == f'{dst_currency.value}{src_currency.value}')   # noqa
            rate = 1.0 / float(rate['price'])
            return rate

    def bid_price(self, src_currency, dst_currency):
        return self.rates(src_currency, dst_currency)

    def ask_price(self, src_currency, dst_currency):
        return self.rates(src_currency, dst_currency)

    def get_transfer_fee(self, dst_currency):
        if dst_currency == Currency.EUR:
            return 0.8
        else:
            return super(BinanceExchange, self).get_transfer_fee(dst_currency)


class MyEtherWallet(CryptoWallet):
    def __init__(self):
        super(MyEtherWallet, self).__init__("MEW")

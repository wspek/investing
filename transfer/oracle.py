import requests

from transfer.constants import Currency, SATOSHI


class CryptoOracle:
    api_url = 'https://api.coinranking.com/v2'
    coinrank_api_key = 'coinrankingc79b08a6c5bcaab0003acdbd30d88a22821a8ab63fdd5a72'

    @staticmethod
    def exchange_rate(src_currency, dst_currency):
        prices = CryptoOracle._get_prices()

        if dst_currency == Currency.USD:
            return prices[src_currency.value]
        elif src_currency == Currency.USD:
            return 1.0 / prices[dst_currency.value]
        else:
            return prices[src_currency] / prices[dst_currency.value]

    @staticmethod
    def _get_prices():
        url = f'{CryptoOracle.api_url}/coins'
        coins = requests.get(url=url, headers={'x-access-token': CryptoOracle.coinrank_api_key}).json()

        return {coin['symbol']: float(coin['price']) for coin in coins['data']['coins']}


class BitcoinOracle(CryptoOracle):
    fee_url = 'https://api.blockchain.info/mempool/fees'

    @staticmethod
    def fee(inputs=1, outputs=2, priority=True):
        transaction_size_bytes = (inputs * 148) + (outputs * 34) + 10 + inputs

        fees = requests.get(BitcoinOracle.fee_url).json()
        fee_in_satoshis = fees['priority'] if priority else fees['regular']

        return (fee_in_satoshis * transaction_size_bytes) * SATOSHI

    @staticmethod
    def exchange_rate(dst_currency=Currency.USD):
        return CryptoOracle.exchange_rate(src_currency=Currency.BTC, dst_currency=dst_currency)


class EthereumOracle:
    fee_url = 'https://ycharts.com/charts/fund_data.json?securities=id:I:EATFND,include:true,,'

    @staticmethod
    def fee(expressed_in=Currency.ETH):
        fees = requests.get(EthereumOracle.fee_url).json()
        fee = fees['chart_data'][0][0]['last_value']

        if expressed_in == Currency.USD:
            return fee
        elif expressed_in in (Currency.ETH, Currency.DAI, Currency.USDT):
            rate = CryptoOracle.exchange_rate(src_currency=expressed_in, dst_currency=Currency.USD)
            return fee / rate
        else:
            raise ValueError

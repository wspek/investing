import requests


class BitcoinAgent:
    fee_url = 'https://api.blockchain.info/mempool/fees'

    @staticmethod
    def fee(inputs=1, outputs=2, priority=True):
        transaction_size_bytes = (inputs * 148) + (outputs * 34) + 10 + inputs

        fees = requests.get('https://api.blockchain.info/mempool/fees').json()
        fee_in_satoshis = fees['priority'] if priority else fees['regular']

        return fee_in_satoshis * transaction_size_bytes

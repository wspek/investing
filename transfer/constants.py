from enum import Enum
from dataclasses import dataclass


SATOSHI = 0.00000001


class Currency(Enum):
    ARS = 'ARS'
    EUR = 'EUR'
    USD = 'USD'
    BTC = 'BTC'
    ETH = 'ETH'
    DAI = 'DAI'
    USDT = 'USDT'
    PAX = 'PAX'


class Brokers(Enum):
    RIPIO = 'ripio'
    SATOSHI_TANGO = 'satoshi_tango'
    BUENBIT = 'buenbit'
    QUBIT = 'qubit'
    BITSO = 'bitso'
    BITEX = 'bitex'
    ARGENBTC = 'argenbtc'
    BUDA = 'buda'
    CRYPTOMARKET = 'cryptomarket'
    IBITT = 'ibitt'
    BITONIC = 'bitonic'
    BITVAVO = 'bitvavo'

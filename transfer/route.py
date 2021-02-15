from enum import Enum

import transfer.crypto as crypto
import transfer.bank as bank
from transfer.constants import Currency


class Route:
    def __init__(self):
        self._nodes = []
        self._transactions = []

    def add_node(self, account):
        self._nodes.append(account)

        if len(self._nodes) > 1:
            src_account = self._nodes[-2]
            dst_account = self._nodes[-1]

            if src_account.currency == dst_account.currency:
                self._transactions.append(Transfer(src_account=src_account, dst_account=dst_account))
            else:
                self._transactions.append(Exchange(src_account=src_account, dst_account=dst_account))

    def send(self, amount):
        self._transactions[0].amount = amount

        for i, tx in enumerate(self._transactions, start=1):
            tx.reverse = False
            amount_transferred = tx.execute()
            print(f'{tx}: {amount_transferred}')

            try:
                self._transactions[i].amount = amount_transferred
            except IndexError:
                return amount_transferred

    def receive(self, amount):
        self._transactions[-1].amount = amount

        for i, tx in enumerate(reversed(self._transactions), start=2):
            tx.reverse = True
            amount_transferred = tx.execute()
            print(f'{tx}: {amount_transferred}')

            try:
                self._transactions[-i].amount = amount_transferred
            except IndexError:
                return amount_transferred


class Transfer:
    def __init__(self, amount=0.0, src_account=None, dst_account=None):
        self.amount = amount
        self.src_account = src_account
        self.dst_account = dst_account
        self.executing_institution = self.src_account.institution
        self.reverse = False

    def execute(self):
        return self.executing_institution.execute_transfer(self)

    def move(self, amount):
        self.src_account.withdraw(amount)
        self.dst_account.deposit(amount)

        return amount

    def __str__(self):
        return f'{self.src_account.name} > {self.dst_account.name}'


class Exchange:
    def __init__(self, amount=0.0, src_account=None, dst_account=None):
        self.amount = amount
        self.src_account = src_account
        self.dst_account = dst_account
        self.executing_institution = self.src_account.institution

    def execute(self):
        return self.executing_institution.execute_exchange(self)

    def __str__(self):
        return f'{self.src_account.name} > {self.dst_account.name}'


class Direction(Enum):
    SEND = 'send'
    RECEIVE = 'receive'


class Institution(Enum):
    BANCO_GALICIA = "Banco Galicia ARG"
    RABOBANK = "Rabobank NL"
    LETS_BIT = "Let's Bit"
    RIPIO = "Ripio"
    MEW = "MyEtherWallet"
    BITVAVO = "Bitvavo"
    BINANCE = "Binance"


institutions = {
    Institution.BANCO_GALICIA: bank.BancoGalicia,
    Institution.RABOBANK: bank.Rabobank,
    Institution.LETS_BIT: crypto.LetsBitExchange,
    Institution.RIPIO: crypto.RipioExchange,
    Institution.MEW: crypto.MyEtherWallet,
    Institution.BITVAVO: crypto.BitvavoExchange,
    Institution.BINANCE: crypto.BinanceExchange,
}


def process_route(direction, amount, hops):
    route = Route()

    for hop in hops:
        institution = institutions[Institution(hop["institution"])]()
        account = institution.create_account(Currency(hop["currency"]))
        route.add_node(account)

    if Direction(direction) == Direction.SEND:
        reciprocal_amount = route.send(amount)
        effective_rate = amount / reciprocal_amount
    else:
        reciprocal_amount = route.receive(amount)
        effective_rate = reciprocal_amount / amount

    return {
        'direction': direction,
        'src_currency': hops[0]["currency"],
        'dst_currency': hops[-1]["currency"],
        'amount': amount,
        'reciprocal_amount': reciprocal_amount,
        'effective_rate': effective_rate
    }

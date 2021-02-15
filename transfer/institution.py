from collections import defaultdict

from transfer.constants import Currency


class Institution:
    available_pairs = []

    def __init__(self, name):
        self.name = name
        self.accounts = []
        self._exchange_rates = defaultdict(list)

    @staticmethod
    def is_crypto(currency):
        return currency in (Currency.BTC, Currency.DAI, Currency.ETH, Currency.USDT, Currency.PAX)

    def get_pair(self, src_currency, dst_currency):
        if (src_currency, dst_currency) in self.available_pairs:
            return src_currency, dst_currency
        elif (dst_currency, src_currency) in self.available_pairs:
            return dst_currency, src_currency
        else:
            raise ValueError

    def create_account(self, currency, initial_balance=0.0):
        account = Account(institution=self, currency=currency, initial_balance=initial_balance)
        self.accounts.append(account)

        return account

    def execute_transfer(self, transfer):
        if transfer.reverse:
            transfer.dst_account.withdraw(transfer.amount)
            transfer.src_account.deposit(transfer.amount)
        else:
            transfer.src_account.withdraw(transfer.amount)
            transfer.dst_account.deposit(transfer.amount)

        return transfer.amount

    def execute_exchange(self, exchange):
        raise NotImplementedError

    def __str__(self):
        return self.name


class Account:
    def __init__(self, institution, currency, initial_balance=0.0):
        self.number = len(institution.accounts) + 1
        self.name = f'{institution.name}:{currency.value}'
        self.institution = institution
        self.currency = currency
        self.balance = initial_balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        self.balance -= amount

    def __str__(self):
        return self.name

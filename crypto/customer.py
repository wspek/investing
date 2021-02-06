from crypto.broker import PriceType


class Customer:
    def want_to_send(self, amount, src_currency, dst_currency, tx_currency, src_broker, dst_broker):
        pass

    def want_to_receive(self, amount, src_currency, dst_currency, tx_currency, src_broker, dst_broker):
        src_broker = src_broker()
        dst_broker = dst_broker()

        src_broker.sync_exchange_rate(src_currency, tx_currency)
        dst_broker.sync_exchange_rate(tx_currency, dst_currency)

        # TX-currency to pay at destination
        tx_to_send = dst_broker.sell_to_receive(amount=amount, of_currency=dst_currency, for_currency=tx_currency)
        src_to_send = src_broker.buy(amount=tx_to_send, of_currency=tx_currency, for_currency=src_currency)

        return {
            'send': f'{src_to_send} {src_currency.value}',
            'receive': f'{amount} {dst_currency.value}',
            'src': f'[{src_broker.name}] {src_broker.exchange_rate(PriceType.ASK, src_currency, tx_currency)}',    # noqa
            'dst': f'[{dst_broker.name}] {dst_broker.exchange_rate(PriceType.BID, tx_currency, dst_currency)}',    # noqa
        }

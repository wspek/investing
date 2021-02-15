from crypto.customer import Customer
from crypto.constants import Currency
import crypto.broker as broker

AMOUNT = 409

if __name__ == '__main__':
    customer = Customer()

    data = customer.want_to_receive(amount=AMOUNT,
                                    src_currency=Currency.ARS,
                                    dst_currency=Currency.EUR,
                                    tx_currency=Currency.BTC,
                                    src_broker=broker.RipioBroker,
                                    dst_broker=broker.BitvavoBroker)

    print(data)

    data = customer.want_to_receive(amount=AMOUNT,
                                    src_currency=Currency.ARS,
                                    dst_currency=Currency.EUR,
                                    tx_currency=Currency.BTC,
                                    src_broker=broker.LetsBit,
                                    dst_broker=broker.BitvavoBroker)

    print(data)

    data = customer.want_to_receive(amount=AMOUNT,
                                    src_currency=Currency.ARS,
                                    dst_currency=Currency.EUR,
                                    tx_currency=Currency.DAI,
                                    src_broker=broker.RipioBroker,
                                    dst_broker=broker.BitvavoBroker)

    print(data)

    data = customer.want_to_receive(amount=AMOUNT,
                                    src_currency=Currency.ARS,
                                    dst_currency=Currency.EUR,
                                    tx_currency=Currency.DAI,
                                    src_broker=broker.LetsBit,
                                    dst_broker=broker.BitvavoBroker)

    print(data)

    #
    # for broker_arg in brokers_arg:
    #     for broker_nl in brokers_nl:
    #         print(f'\n*** {broker_arg.value} to {broker_nl.value} ***')
    #         print(client.get_btc_price(from_broker=broker_arg))
    #         cost_in_ars = client.receive_amount(euros=EUR_TO_RECEIVE, broker_arg=broker_arg, broker_nl=broker_nl)
    #         print('{} ARS > {} BTC > {} EUR'.format(cost_in_ars['ARS'], cost_in_ars['BTC'], EUR_TO_RECEIVE))
    #         print(cost_in_ars)
    #         cost_per_eur = cost_in_ars['ARS'] / EUR_TO_RECEIVE
    #         print(f'EUR/ARS ~ {cost_per_eur}')
    #
    # rcv_in_eur = client.send_amount(pesos=100000, broker_arg=Brokers.RIPIO, broker_nl=Brokers.BITVAVO)
    # print(rcv_in_eur)

# Copyright 2017 Ihar Hrachyshka <ihar.hrachyshka@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time

# todo: transform into exchange agnostic exceptions
from poloniex import exceptions as plx_exc

from cryptotrade._exchanges import polo
from cryptotrade.cli import trade_base
from cryptotrade import exchange
from cryptotrade import trader


class TradeExecuteCommand(trade_base.BaseTradeCommand):
    '''execute trade strategy'''

    def get_parser(self, prog_name):
        parser = super(TradeExecuteCommand, self).get_parser(prog_name)
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help="don't ask to confirm before creating orders")
        parser.add_argument(
            '-i',
            dest='interval',
            required=True,
            type=int,
            # todo: untangle from poloniex exchange
            choices=polo.Poloniex.CANDLESTICKS,
            help='time since previous assessment')
        return parser

    def take_action(self, parsed_args):
        while True:
            # flag indicating whether we are done with all trading for the
            # cycle and can bail out
            exit = False

            ex = exchange.get_exchange_by_name(
                self.app.cfg, parsed_args.exchange)

            # cancel all orders before proceeding
            orders = ex.get_orders()
            for _, orders_ in orders.items():
                for order in orders_:
                    order_number = order['orderNumber']
                    attempts = 0
                    while True:
                        if attempts == 3:
                            # apparently the order is no longer
                            break
                        try:
                            ex.cancel_order(order)
                            break
                        except plx_exc.PoloniexCommandException as e:
                            print('Failed to cancel order #%(order_number)d: '
                                  '%(e)s' %
                                  {'order_number': order_number, 'e': e})
                            attempts += 1
                            continue
                    print('Cancelled order %d' % order_number)

            gold = 'BTC'

            targets = parsed_args.targets
            weights = parsed_args.weights
            balances = exchange.get_global_balance(self.app.cfg)

            now = time.time()
            in_past = now - parsed_args.interval

            old_rates = ex.get_opening_rates(
                gold, list(set(balances.keys() + targets)),
                parsed_args.interval,
                in_past, now)
            assert \
                all([len(v) == 1 for v in old_rates.values()]), \
                "too many rate results"

            all_currencies = list(set(balances.keys() + targets))
            new_rates = ex.get_closing_rates(
                gold, all_currencies,
                parsed_args.interval,
                in_past, now)
            assert \
                all([len(v) == 1 for v in old_rates.values()]), \
                "too many rate results"

            rates = {}
            for target in all_currencies:
                rates[target] = old_rates[target] + new_rates[target]

            strategy = trader.get_strategy(parsed_args.strategy)
            ops, _ = strategy.trade(
                targets, weights, gold, ex.get_fee(), balances, rates)

            _, ops_ = ops[-1]  # we are interested in the last 'trade' only
            if not parsed_args.force:
                if ops_:
                    print('The following trade orders are to be schedule:')
                    for o in ops_:
                        d = {'gold': gold,
                             'op': o.op,
                             'rate': o.rate,
                             'gold_amount': o.gold_amount,
                             'alt_amount': o.alt_amount,
                             'alt': o.alt}
                        if o.op == trader.SELL_OP:
                            print(' * buy %(gold_amount).4f %(gold)s '
                                  'with %(alt_amount).4f %(alt)s '
                                  '(rate: %(rate)s)' % d)
                        else:
                            print(' * sell %(gold_amount).4f %(gold)s '
                                  'for %(alt_amount).4f %(alt)s '
                                  '(rate: %(rate)s)' % d)
                    answer = raw_input("Would you like to proceed? ")
                    if answer not in 'yY':
                        return

            sell_ops = [o for o in ops_ if o.op == trader.SELL_OP]
            buy_ops = [o for o in ops_ if o.op == trader.BUY_OP]

            def create_orders(ops):
                for o in ops:
                    if o.scheduled:
                        continue
                    # poloniex doesn't support BTC amounts less than 0.0001
                    if o.alt_amount * o.rate < 0.0001:
                        print(
                            "Ignore request for %f %s due to negligible size" %
                            (o.alt_amount, o.alt))
                        o.scheduled = True
                        continue
                    alt_amount = "%.8f" % o.alt_amount

                    # try to outbid others
                    rate = (
                        ex.get_rate(gold, o.alt) +
                        (0.00000001 if o.op == trader.BUY_OP else -0.00000001)
                    )
                    if rate / o.rate <= 1.002:
                        print('overriding exchange rate to outbid others')
                        rate = o.rate
                    else:
                        print('we cannot afford ticker rate, use '
                              'pre-calculated rate and hope for the best')

                    method = ex.sell if o.op == trader.SELL_OP else ex.buy
                    try:
                        order = method(gold, o.alt, o.rate, alt_amount)
                        o.scheduled = True
                    except plx_exc.PoloniexCommandException as e:
                        print('Failed to create %(op)s order for '
                              '%(alt_amount).4f %(alt)s: %(e)s' %
                              {
                                  'op': o.op,
                                  'alt_amount': o.alt_amount,
                                  'alt': o.alt,
                                  'e': e,
                              })
                        continue

                    print('Placed order %(order_number)d to '
                          '%(op)s %(alt_amount).4f %(alt)s' %
                          {
                              'order_number': order['orderNumber'],
                              'op': o.op,
                              'alt_amount': o.alt_amount,
                              'alt': o.alt,
                          })

            time_waited = 0
            while True:
                # if orders don't execute for a while, respin trading
                if time_waited > 300:
                    break

                if any([not o.scheduled for o in sell_ops]):
                    create_orders(sell_ops)
                if any([not o.scheduled for o in buy_ops]):
                    create_orders(buy_ops)

                time.sleep(10)
                time_waited += 10

                orders = ex.get_orders()
                if not orders and all([o.scheduled for o in ops_]):
                    print('All orders executed!')
                    exit = True
                    break

            if exit:
                break

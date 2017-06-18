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

import collections
import time

from cliff.lister import Lister
from cryptotrade import polo_exchange
from cryptotrade import trader


class TradeAssessCommand(Lister):
    '''assess trade strategy'''

    def get_parser(self, prog_name):
        parser = super(TradeAssessCommand, self).get_parser(prog_name)
        parser.add_argument(
            '-b',
            dest='balances',
            action='append',
            metavar='CURRENCY=AMOUNT',
            help='currency balances')
        parser.add_argument(
            '-i',
            dest='interval',
            metavar='MINUTES',
            required=True,
            type=int,
            # todo: untangle from poloniex exchange
            choices=polo_exchange.Poloniex.CANDLESTICKS,
            help='time interval between assessment iterations')
        parser.add_argument(
            '-p',
            dest='period',
            metavar='DAYS',
            required=True,
            type=float,
            help='past time period to assess')
        parser.add_argument(
            '-s',
            dest='strategy',
            choices=trader.list_strategy_names(),
            help='trading strategy to assess')
        parser.add_argument(
            '-t',
            dest='targets',
            action='append',
            metavar='CURRENCY=WEIGHT',
            help='target weight per currency')
        return parser

    def take_action(self, parsed_args):
        # todo: abstract exchange from the command
        ex = polo_exchange.Poloniex(self.app.cfg)

        now = time.time()
        in_past = now - 60 * 60 * 24 * parsed_args.period

        gold = 'BTC'

        targets = {}
        total_weight = 0
        for target in parsed_args.targets:
            currency, weight = target.split('=')
            weight = float(weight)
            total_weight += weight
            targets[currency] = weight
        if total_weight != 1.0:
            raise RuntimeError("error: weights don't add up to 1")

        if parsed_args.balances:
            balances = collections.defaultdict(float)
            for balance in parsed_args.balances:
                currency, amount = balance.split('=')
                amount = float(amount)
                balances[currency] = amount
        else:
            balances = ex.get_balances()

        old_worth_btc = ex.get_worth('BTC', balances=balances)
        old_worth_usd = ex.get_worth('USD', balances=balances)

        rates = ex.get_closing_rates(
            gold, list(targets.keys()),
            parsed_args.interval,
            in_past, now)

        strategy = trader.get_strategy(parsed_args.strategy)
        strategy.trade(targets, gold, ex.get_fee(), balances, rates)

        new_worth_btc = ex.get_worth('BTC', balances=balances)
        new_worth_usd = ex.get_worth('USD', balances=balances)

        # todo: maybe handle division by zero
        profit = (new_worth_btc - old_worth_btc) / old_worth_btc * 100

        return (
            ('', 'HODL', 'w/strategy'),
            (('USD', old_worth_usd, new_worth_usd),
             ('BTC', old_worth_btc, new_worth_btc),
             ('%', '100%', '%s%%' % (100 + profit)))
        )

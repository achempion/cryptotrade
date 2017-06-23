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

from cliff.lister import Lister

from cryptotrade._exchanges import polo
from cryptotrade import exchange
from cryptotrade import trader
from cryptotrade.cli import trade_base


class TradeAssessCommand(Lister, trade_base.BaseTradeCommand):
    '''assess trade strategy'''

    def get_parser(self, prog_name):
        parser = super(TradeAssessCommand, self).get_parser(prog_name)
        parser.add_argument(
            '-i',
            dest='interval',
            required=True,
            type=int,
            # todo: untangle from poloniex exchange
            choices=polo.Poloniex.CANDLESTICKS,
            help='time interval between assessment iterations')
        parser.add_argument(
            '-p',
            dest='period',
            metavar='DAYS',
            required=True,
            type=float,
            help='past time period to assess')
        return parser

    def take_action(self, parsed_args):
        ex = exchange.get_exchange_by_name(self.app.cfg, parsed_args.exchange)

        now = time.time()
        in_past = now - 60 * 60 * 24 * parsed_args.period

        gold = 'BTC'

        targets = self.get_targets(parsed_args)
        balances = self.get_balances(parsed_args)

        old_worth_btc = ex.get_worth('BTC', balances=balances)
        old_worth_usd = ex.get_worth('USD', balances=balances)

        rates = ex.get_closing_rates(
            gold, list(set(balances.keys() + targets.keys())),
            parsed_args.interval,
            in_past, now)

        strategy = trader.get_strategy(parsed_args.strategy)
        _, new_balances = strategy.trade(
            targets, gold, ex.get_fee(), balances, rates)

        new_worth_btc = ex.get_worth('BTC', balances=new_balances)
        new_worth_usd = ex.get_worth('USD', balances=new_balances)

        if old_worth_btc:
            profit = (new_worth_btc - old_worth_btc) / old_worth_btc * 100
        else:
            profit = 0

        return (
            ('', '-', parsed_args.strategy),
            (('USD', old_worth_usd, new_worth_usd),
             ('BTC', old_worth_btc, new_worth_btc),
             ('%', '100%', '%s%%' % (100 + profit)))
        )

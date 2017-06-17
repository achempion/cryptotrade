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
from cryptotrade import polo_exchange
from cryptotrade import trader


class TradeAssessCommand(Lister):
    '''assess trade strategy'''

    def take_action(self, parsed_args):
        # todo: abstract exchange from the command
        ex = polo_exchange.Poloniex(self.app.cfg)

        # todo: allow to specify period via cli
        now = time.time()
        in_past = now - 60 * 60 * 24 * 180  # 180 days

        gold = 'BTC'

        # todo: allow to specify balance via cli
        # todo: allow to specify candlestick length via cli
        # todo: allow to specify targets via cli
        balances = ex.get_balances()

        old_worth_btc = ex.get_worth('BTC', balances=balances)
        old_worth_usd = ex.get_worth('USD', balances=balances)

        targets = self.app.cfg['core']['target']
        rates = ex.get_closing_rates(
            gold, list(targets.keys()),
            60 * 60 * 4,  # use 4h candlesticks
            in_past, now)

        # todo: allow to pick strategy via cli
        trader.trade(
            targets, gold, ex.get_fee(),
            balances, rates, trader.balance_trader)

        new_worth_btc = ex.get_worth('BTC', balances=balances)
        new_worth_usd = ex.get_worth('USD', balances=balances)

        # todo: maybe handle division by zero
        profit = (new_worth_btc - old_worth_btc) / old_worth_btc * 100

        return (
            ('', 'HODL', 'w/strategy'),
            (('USD', old_worth_usd, new_worth_usd),
             ('BTC', old_worth_btc, new_worth_btc),
             ('%', '100%', '%s%%' % profit))
        )
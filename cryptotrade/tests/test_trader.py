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

import random
import unittest

from cryptotrade import trader


class TestNoopStrategy(unittest.TestCase):
    def test_does_nothing(self):
        balances = {'BTC': 5, 'ETH': 10, 'XMR': 20}
        orig_balances = balances.copy()
        fake_rates = {
            currency: [
                random.random() for i in range(100)
            ]
            for currency in balances.keys()
        }

        fee = 0.0025
        targets = {'BTC': 0.5, 'ETH': 0.25, 'XMR': 0.25}
        strategy = trader.NoopStrategy()
        strategy.trade(targets, 'BTC', fee, balances, fake_rates)
        self.assertEqual(orig_balances, balances)


class TestBalanceTrader(unittest.TestCase):
    def test_balance_trader_balances(self):
        targets = {'ETH': 0.5, 'BTC': 0.25, 'LTC': 0.25}
        gold = 'BTC'
        fee = 0.0  # to simplify matters
        balances = {'BTC': 1000.0, 'ETH': 0.0, 'LTC': 0.0}
        fake_rates = {
            'ETH': [0.5,  1.0, 0.5],
            'LTC': [0.5, 0.25, 1.0],
            'BTC': [1.0,  1.0, 1.0],
        }

        strategy = trader.BCRStrategy()
        ops, new_balances = strategy.trade(
            targets, gold, fee, balances, fake_rates)

        # -> BTC = 1000, ETH = 0, LTC = 0 (total 1000 BTC)
        #
        # iter 1: 500 BTC -> 1000 ETH; 250 BTC -> 500 LTC
        # -> BTC = 250, ETH = 1000, LTC = 500 (total 1375 BTC)
        #
        # iter 2: 312.5 ETH -> 312.5 BTC; 218.75 BTC -> 875 LTC
        # -> BTC = 343.75, ETH = 687.5, LTC = 1375 (total 2062.5 BTC)
        #
        # iter 3: 687.5 BTC -> 1375 ETH; 859.375 LTC -> 859.375 BTC
        # -> BTC = 515.625, ETH = 2062.5, LTC = 515.625
        self.assertEqual(
            {'BTC': 515.625, 'ETH': 2062.5, 'LTC': 515.625}, new_balances)


class TestStrategy(unittest.TestCase):

    class FakeStrategy(trader.Strategy):

        def __init__(self, *args, **kwargs):
            self.calls = []

        def get_targets(self, targets, gold, balances, rates, i):
            # we explicitly ignore balances because they depend on targets
            # under test that are random
            self.calls.append((targets, gold, rates, i))
            return targets

    def test_trade_number_of_callbacks(self):
        balances = {'BTC': 5, 'ETH': 10, 'XMR': 20}
        targets = {'BTC': 0.5, 'ETH': 0.25, 'XMR': 0.25}
        fake_rates = {
            currency: [
                random.random() for i in range(5)
            ]
            for currency in balances.keys()
        }
        gold = 'BTC'
        fee = 0.0025

        strategy = self.FakeStrategy()
        strategy.trade(targets, gold, fee, balances, fake_rates)
        self.assertEqual(
            [
                (targets, gold, fake_rates, i)
                for i in range(len(fake_rates[gold]))
            ], strategy.calls)

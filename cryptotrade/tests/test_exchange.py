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

from cryptotrade import exchange


class TestGetWorth(unittest.TestCase):

    class FakeExchange(exchange.Exchange):

        def get_balances(self):
            return {'BTC': 5, 'XMR': 10, 'ETH': 100}

        def get_rate(self, from_, to_):
            if from_ == 'BTC':
                if to_ == 'BTC':
                    return 1
                elif to_ == 'XMR':
                    return 0.1
                else:
                    return 0.01
            else:  # BTC -> USD
                return 2500

        def get_fee(self):
            return 0.0

        # needed to fulfill abstract interface
        def cancel_all_orders(self):
            return NotImplemented

        def get_candlesticks(self, from_, to_, period, start, end):
            return [
                {'close': random.random()}
                for _ in range(start, end, period)
            ]

        def buy(self, from_, to_, rate, amount):
            return random.randrange(100)

        def sell(self, from_, to_, rate, amount):
            return random.randrange(100)

    def setUp(self):
        super(TestGetWorth, self).setUp()
        config = object()
        self.exchange = self.FakeExchange(config)

    def test_get_worth_btc(self):
        res = self.exchange.get_worth('BTC')
        self.assertEqual(7, res)

    def test_get_worth_usd(self):
        res = self.exchange.get_worth('USD')
        self.assertEqual(7 * 2500, res)

    def test_get_worth_custom_balances(self):
        balances = {'BTC': 10, 'ETH': 200, 'XMR': 30}
        res = self.exchange.get_worth('BTC', balances=balances)
        self.assertEqual(15, res)

    def test_get_worth_custom_balances_usd(self):
        balances = {'BTC': 10, 'ETH': 200, 'XMR': 30}
        res = self.exchange.get_worth('USD', balances=balances)
        self.assertEqual(15 * 2500, res)

    def test_get_closing_rates(self):
        res = self.exchange.get_closing_rates(
            'BTC', ('XMR', 'ETH'), 300, 0, 0 + 1500)
        for k, v in res.items():
            self.assertEqual(1500/300, len(v))
        self.assertEqual([1] * len(v), res['BTC'])

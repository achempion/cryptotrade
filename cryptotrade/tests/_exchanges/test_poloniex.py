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

import mock
import unittest

from cryptotrade._exchanges import polo


class TestPoloniex(unittest.TestCase):

    def setUp(self):
        super(TestPoloniex, self).setUp()
        conf = {
            'poloniex': {'api_key': 'fakekey', 'api_secret': 'fakesecret'}
        }
        self.plx = polo.Poloniex(conf)

    def test_cancel_order(self):
        order = {'orderNumber': 100}
        with mock.patch.object(self.plx.private, 'cancelOrder') as cancel_mock:
            self.plx.cancel_order(order)
        cancel_mock.assert_called_with(100)

    def test_get_orders(self):
        api_orders = {
            'BTC_XMR': [{'orderNumber': 10}, {'orderNumber': 20}],
            'BTC_ETH': [{'orderNumber': 50}],
            'BTC_FCT': [],
        }
        with mock.patch.object(self.plx.private, 'returnOpenOrders',
                               return_value=api_orders):
            orders = self.plx.get_orders()
        expected = api_orders.copy()
        # we should not receive pairs with no orders
        expected.pop('BTC_FCT')
        self.assertEqual(expected, orders)

    def test_get_candlesticks(self):
        with mock.patch.object(self.plx.private, 'returnChartData') as m:
            res = self.plx.get_candlesticks(
                'BTC', 'XMR', period=300, start=0, end=1000)
        m.assert_called_once_with('BTC_XMR', 300, start=0, end=1000)
        self.assertEqual(m.return_value, res)

    def test_get_balances(self):
        balances = {'BTC': 1.0, 'XMR': 2.5, 'ETH': 0.0}
        with mock.patch.object(self.plx.private, 'returnBalances',
                               return_value=balances):
            res = self.plx.get_balances()
        # check that we filtered out currencies that are not owned
        self.assertEqual({'BTC': 1.0, 'XMR': 2.5}, res)

    def test_get_rate(self):
        ticker = {
            'BTC_LTC': {'lowestAsk': 0.0251, 'highestBid': 0.0251},
            'BTC_NXT': {'lowestAsk': 0.1234, 'highestBid': 0.1234},
        }
        with mock.patch.object(self.plx.private, 'returnTicker',
                               return_value=ticker):
            res = self.plx.get_rate('BTC', 'LTC')
        self.assertEqual(0.0251, res)

    def test_ticker_cache(self):
        with mock.patch.object(self.plx.private, 'returnTicker') as m:
            self.plx._ticker()
            self.plx._ticker()
        # second call hasn't called to external api due to cache
        m.assert_called_once()

    def test_get_fee(self):
        fee_info = {
            "makerFee": "0.00140000",
            "takerFee": "0.00240000",
            "thirtyDayVolume": "612.00248891",
            "nextTier": "1200.00000000"
        }
        with mock.patch.object(self.plx.private, 'returnFeeInfo',
                               return_value=fee_info):
            self.assertEqual(0.0024, self.plx.get_fee())

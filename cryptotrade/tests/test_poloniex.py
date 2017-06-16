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

from unittest import mock
import unittest

from cryptotrade import poloniex


class TestPoloniex(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.plx = poloniex.Poloniex('fakesecret', 'fakekey')

    def test_cancel_all_orders(self):
        orders = {
            'BTC_XMR': [{'orderNumber': 10}, {'orderNumber': 20}],
            'BTC_ETH': [{'orderNumber': 50}],
            'BTC_FCT': [],
        }
        with mock.patch.object(self.plx.private, 'returnOpenOrders',
                               return_value=orders):
            with mock.patch.object(self.plx.private,
                                   'cancelOrder') as cancel_mock:
                self.plx.cancel_all_orders()
        cancel_mock.assert_has_calls(
            [mock.call(num) for num in (10, 20, 50)], any_order=True)

    def test_get_candlesticks(self):
        with mock.patch.object(self.plx.public, 'returnChartData') as m:
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
            'BTC_LTC': {'last': 0.0251},
            'BTC_NXT': {'last': 0.1234},
        }
        with mock.patch.object(self.plx.public, 'returnTicker',
                               return_value=ticker):
            res = self.plx.get_rate('BTC', 'LTC')
        self.assertEqual(0.0251, res)

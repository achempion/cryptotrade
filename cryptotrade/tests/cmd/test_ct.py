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
import os
import tempfile
import unittest

from cryptotrade.cmd import ct
from cryptotrade import exchange


class TestMain(unittest.TestCase):
    def setUp(self):
        super(TestMain, self).setUp()
        self.fp, self.fname = tempfile.mkstemp()
        os.close(self.fp)

    def tearDown(self):
        os.remove(self.fname)
        super(TestMain, self).tearDown()

    def test_main(self):
        contents = (
            '[poloniex]\n'
            'api_key = fakekey\n'
            'api_secret = fakesecret\n'
        )
        with open(self.fname, 'w') as f:
            f.write(contents)
        with mock.patch('poloniex.Poloniex._private'):
            self.assertEqual(0, ct.main(args=['-c', self.fname]))


class Test_ParseArgs(unittest.TestCase):
    def test_custom_config_file(self):
        filename = 'other'
        args = ct._parse_args(['-c', filename])
        self.assertEqual(filename, args.config_file)


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

        # needed to fulfill abstract interface
        def cancel_all_orders(self):
            return NotImplemented

        # needed to fulfill abstract interface
        def get_candlesticks(self, from_, to_, period, start, end):
            return NotImplemented

    def setUp(self):
        super(TestGetWorth, self).setUp()
        config = object()
        self.exchange = self.FakeExchange(config)

    def test_get_worth_btc(self):
        res = ct.get_worth(self.exchange, 'BTC')
        self.assertEqual(7, res)

    def test_get_worth_usd(self):
        res = ct.get_worth(self.exchange, 'USD')
        self.assertEqual(7 * 2500, res)

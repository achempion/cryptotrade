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

from coinbase.wallet import client as cclient

from cryptotrade import exchange


class MissingCoinbaseApiKey(Exception):
    message = 'Missing API key or secret in the configuration file.'


class Coinbase(exchange.Exchange):

    CANDLESTICKS = (300, 900, 1800, 7200, 14400, 86400)

    def __init__(self, conf):
        super(Coinbase, self).__init__(conf)
        coinbase_conf = conf['coinbase']
        for key in ('api_key', 'api_secret'):
            if key not in coinbase_conf:
                raise MissingCoinbaseApiKey
        self.client = cclient.Client(
            api_key=coinbase_conf['api_key'].encode('utf-8'),
            api_secret=coinbase_conf['api_secret'].encode('utf-8'))

    def get_balances(self):
        accounts = self.client.get_accounts()
        res = collections.defaultdict(float)
        for acc in accounts['data']:
            balance = acc['balance']
            amount = float(balance['amount'])
            if amount > 0.0:
                res[balance['currency']] += amount
        return res

    def get_fee(self):
        return NotImplemented

    def get_rate(self, from_, to_):
        return NotImplemented

    def get_candlesticks(self, from_, to_, period, start, end):
        return NotImplemented

    def get_orders(self):
        return NotImplemented

    def cancel_order(self, order):
        return NotImplemented

    def buy(self, from_, to_, rate, amount):
        return NotImplemented

    def sell(self, from_, to_, rate, amount):
        return NotImplemented

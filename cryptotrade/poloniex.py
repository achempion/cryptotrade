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

import poloniex as plx

from cryptotrade import exchange


class Poloniex(exchange.Exchange):

    def __init__(self, api_secret, api_key):
        super().__init__()
        self.public = plx.PoloniexPublic()
        self.private = plx.Poloniex(apikey=api_key, secret=api_secret)

    def get_balances(self):
        balances = self.private.returnBalances()
        return {
            # filter out currencies that we don't own
            k: v for k, v in balances.items() if v
        }

    def get_rate(self, from_, to_):
        ticker = self.public.returnTicker()
        pair = '%s_%s' % (from_, to_)
        return ticker[pair]['last']

    def get_candlesticks(self, from_, to_, period, start, end):
        return self.public.returnChartData(
            '%s_%s' % (from_, to_), period, start=start, end=end)

    def cancel_all_orders(self):
        for currency_pair, orders_ in self.private.returnOpenOrders().items():
            for order in orders_:
                self.private.cancelOrder(order['orderNumber'])

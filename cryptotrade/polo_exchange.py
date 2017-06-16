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

from cached_property import cached_property_with_ttl
from poloniex import poloniex as plx

from cryptotrade import exchange


class MissingPoloniexSection(Exception):
    message = 'Missing [poloniex] section in the configuration file.'


class MissingPoloniexApiKey(Exception):
    message = 'Missing API key or secret in the configuration file.'


class Poloniex(exchange.Exchange):

    def __init__(self, conf):
        super(Poloniex, self).__init__(conf)
        self.public = plx.PoloniexPublic()
        poloniex_conf = conf.get('poloniex')
        if not poloniex_conf:
            raise MissingPoloniexSection
        for key in ('api_key', 'api_secret'):
            if key not in poloniex_conf:
                raise MissingPoloniexApiKey
        self.private = plx.Poloniex(
            apikey=poloniex_conf['api_key'].encode('utf-8'),
            secret=poloniex_conf['api_secret'].encode('utf-8'))

    def get_balances(self):
        balances = self.private.returnBalances()
        return {
            # filter out currencies that we don't own
            k: v for k, v in balances.items() if v
        }

    @cached_property_with_ttl(ttl=60)
    def _ticker(self):
        return self.public.returnTicker()

    def get_rate(self, from_, to_):
        ticker = self._ticker
        from_ = from_ if from_ != 'USD' else 'USDT'
        pair = '%s_%s' % (from_, to_)
        return ticker[pair]['last']

    def get_candlesticks(self, from_, to_, period, start, end):
        assert from_ == 'BTC', 'poloneix has pairs for BTC only'
        return self.public.returnChartData(
            '%s_%s' % (from_, to_), period, start=start, end=end)

    def cancel_all_orders(self):
        for currency_pair, orders_ in self.private.returnOpenOrders().items():
            for order in orders_:
                self.private.cancelOrder(order['orderNumber'])

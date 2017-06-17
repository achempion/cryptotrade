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

"""
cryptotrade, the cryptocurrency trading automation tool.
"""

import argparse
import os
import sys
import time

from cliff.app import App
from cliff.commandmanager import CommandManager

from cryptotrade import config
from cryptotrade import polo_exchange
from cryptotrade import trader
from cryptotrade import version


class CtApp(App):

    def __init__(self):
        super(CtApp, self).__init__(
            description=sys.modules[__name__].__doc__,
            version=version.get_version(),
            command_manager=CommandManager('ct.cli'),
            deferred_help=True,
            )


CONFIG_FILE = '.cryptotrade.conf'
CONFIG_PATH = os.path.join(os.path.expanduser('~'), CONFIG_FILE)


def _parse_args(args):
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument(
        '-c', dest='config_file', metavar='FILE', default=CONFIG_PATH,
        help='configuration file to load (default: ~/%s)' % CONFIG_FILE)
    return parser.parse_args(args)


# todo: replace ct once its features are incorporated into the new cli manager
def new_main(argv=sys.argv[1:]):
    app = CtApp()
    return app.run(argv)


def main(args=sys.argv[1:]):
    args = _parse_args(args=args)
    conf = config.get_config(args.config_file)
    ex = polo_exchange.Poloniex(conf)

    old_worth = ex.get_worth('BTC')
    print('Your portfolio worth is:')
    print(' * %.4f BTC' % old_worth)
    print(' * %.4f USD' % ex.get_worth('USDT'))

    now = time.time()
    in_past = now - 60 * 60 * 24 * 180  # 180 days

    gold = 'BTC'
    balances = ex.get_balances()
    rates = ex.get_closing_rates(
        gold, list(conf['core']['target'].keys()),
        60 * 60 * 4,  # use 4h candlesticks
        in_past, now)
    trader.trade(
        conf['core']['target'], gold, ex.get_fee(),
        balances, rates, trader.balance_trader)

    new_worth = ex.get_worth('BTC', balances=balances)
    print('Your portfolio is now worth:')
    print(' * %.4f BTC' % new_worth)
    print(' * %.4f USD' % ex.get_worth('USDT', balances=balances))
    print('including %s' % dict(balances))
    print('profit = %.2f%%' % ((new_worth - old_worth) / old_worth * 100))

    return 0

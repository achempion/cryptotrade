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

from cryptotrade import config
from cryptotrade import polo_exchange


CONFIG_FILE = '.cryptotrade.conf'
CONFIG_PATH = os.path.join(os.path.expanduser('~'), CONFIG_FILE)


def _parse_args(args):
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument(
        '-c', dest='config_file', metavar='FILE', default=CONFIG_PATH,
        help='configuration file to load (default: ~/%s)' % CONFIG_FILE)
    return parser.parse_args(args)


def main(args=sys.argv[1:]):
    args = _parse_args(args=args)
    conf = config.get_config(args.config_file)
    ex = polo_exchange.Poloniex(conf)

    print('Your portfolio worth is:')
    print(' * %.4f BTC' % ex.get_worth('BTC'))
    print(' * %.4f USD' % ex.get_worth('USDT'))

    return 0

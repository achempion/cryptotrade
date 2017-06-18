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

from cliff.command import Command

# todo: transform into exchange agnostic exceptions
from poloniex import exceptions as plx_exc

from cryptotrade._exchanges import polo
from cryptotrade import trader


class TradeClearCommand(Command):
    '''clear all outstanding orders'''

    def get_parser(self, prog_name):
        parser = super(TradeClearCommand, self).get_parser(prog_name)
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help="don't ask to confirm before clearing orders")
        return parser

    def take_action(self, parsed_args):
        # todo: abstract exchange from the command
        ex = polo.Poloniex(self.app.cfg)

        orders = ex.get_orders()
        if not parsed_args.force:
            if orders:
                print('The following trade orders are to be cancelled:')
                for pair, orders_ in orders.items():
                    from_, to_ = pair.split('_')
                    for order in orders_:
                        order_type = order['type']
                        d = {
                            'order_number': order['orderNumber'],
                            'amount': order['amount'],
                            'alt': to_,
                            'total': order['total'],
                            'gold': from_,
                        }
                        if order_type == trader.SELL_OP:
                            print('sell #%(order_number)d: '
                                  '%(amount)d %(alt)s -> '
                                  '%(total)s %(gold)s' % d)
                        else:
                            print('buy #%(order_number)d: '
                                  '%(amount)d %(gold)s -> '
                                  '%(total)s %(alt)s' % d)
                answer = raw_input("Would you like to proceed? ")
                if answer not in 'yY':
                    return

        for _, orders_ in orders.items():
            for order in orders_:
                order_number = order['orderNumber']
                try:
                    ex.cancel_order(order)
                except plx_exc.PoloniexCommandException as e:
                    print('Failed to cancel order #%(order_number)d: %(e)s' %
                          {'order_number': order_number, 'e': e})
                    raise

                print('Cancelled order %d' % order_number)

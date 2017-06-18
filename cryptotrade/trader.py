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

import abc

import six
from stevedore.driver import DriverManager
from stevedore.extension import ExtensionManager


STRATEGY_NAMESPACE = 'ct.strategies'


def list_strategy_names():
    return ExtensionManager(STRATEGY_NAMESPACE).entry_points_names()


def get_strategy(name):
    return DriverManager(STRATEGY_NAMESPACE, name, invoke_on_load=True).driver


@six.add_metaclass(abc.ABCMeta)
class Strategy(object):

    # todo: pick better names for public entry points
    @abc.abstractmethod
    def trader(self, targets, gold, fee, balances, rates, i):
        pass

    def trade(self, targets, gold, fee, balances, rates):
        # todo: consider making trade() receive exchange object to extract fees
        # and balances (if not passed) and maybe rates
        for i in range(len(rates[gold])):
            self.trader(targets, gold, fee, balances, rates, i)


class BCRStrategy(Strategy):

    def get_gold_total(self, targets, balances, rates, i):
        return sum(
            balances[currency] * rates[currency][i]
            for currency in targets)

    def trader(self, targets, gold, fee, balances, rates, i):
        gold_total = self.get_gold_total(targets, balances, rates, i)

        for currency, target in targets.items():
            if currency == gold:
                continue

            rate = rates[currency][i]
            gold_worth = balances[currency] * rate
            gold_target = gold_total * target
            gold_diff = abs(gold_target - gold_worth)
            alt_diff = gold_diff / rate

            # todo: use fuzzy comparison
            if gold_worth < gold_target:
                gold_sold = gold_diff * (1 + fee)
                balances[currency] += alt_diff
                balances[gold] -= gold_sold
                # todo: actually trade
                print('buy %.4f %s for %.4f %s (rate: %.6f)' %
                      (alt_diff, currency, gold_sold, gold, rate))
            elif gold_worth > gold_target:
                gold_bought = gold_diff * (1 - fee)
                balances[currency] -= alt_diff
                balances[gold] += gold_bought
                # todo: actually trade
                print('sell %.4f %s for %.4f %s (rate: %.6f)' %
                      (alt_diff, currency, gold_bought, gold, rate))


class NoopStrategy(Strategy):
    def trader(self, targets, gold, fee, balances, rates, i):
        pass

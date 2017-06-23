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
import collections

from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
import six
from stevedore.driver import DriverManager
from stevedore.extension import ExtensionManager


STRATEGY_NAMESPACE = 'ct.strategies'

SELL_OP = 'sell'
BUY_OP = 'buy'

TradeOp = collections.namedtuple(
    'TradeOp', ('op', 'gold_amount', 'alt_amount', 'alt', 'rate'))


def list_strategy_names():
    return ExtensionManager(STRATEGY_NAMESPACE).entry_points_names()


def get_strategy(name):
    return DriverManager(STRATEGY_NAMESPACE, name, invoke_on_load=True).driver


@six.add_metaclass(abc.ABCMeta)
class Strategy(object):

    @abc.abstractmethod
    def get_weights(self, targets, weights, gold, balances, rates, i):
        pass

    @staticmethod
    def get_gold_total(balances, rates, i):
        return sum(
            balances[currency] * rates[currency][i]
            for currency in balances)

    def get_ops(self, targets, weights, gold, fee, balances, rates, i):
        ops = []
        balances = balances.copy()

        gold_total = self.get_gold_total(balances, rates, i)
        for currency, target in zip(targets, weights):
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
                ops.append(
                    TradeOp(
                        op=BUY_OP,
                        gold_amount=gold_sold,
                        alt_amount=alt_diff,
                        alt=currency,
                        rate=rate))
            elif gold_worth > gold_target:
                gold_bought = gold_diff * (1 - fee)
                ops.append(
                    TradeOp(
                        op=SELL_OP,
                        gold_amount=gold_bought,
                        alt_amount=alt_diff,
                        alt=currency,
                        rate=rate))
        return ops

    def apply_ops(self, gold, balances, ops):
        balances = balances.copy()
        for op in ops:
            if op.op == SELL_OP:
                balances[op.alt] -= op.alt_amount
                balances[gold] += op.gold_amount
            else:
                balances[op.alt] += op.alt_amount
                balances[gold] -= op.gold_amount
        return balances

    # todo: consider making trade() receive exchange object to extract fees
    # and balances (if not passed) and maybe rates
    def trade(self, targets, weights, gold, fee, balances, rates):
        ops = []
        balances = balances.copy()
        for i in range(len(rates[gold])):
            # calculate new weights
            weights = self.get_weights(
                targets, weights, gold, balances, rates, i)
            # todo: revisit the rounding workaround
            assert \
                round(sum(weights), 5) == round(1.0, 5), \
                "new targets don't add up to 1.0"

            # produce buy/sell operations based on current balance and targets
            ops_ = self.get_ops(
                targets, weights, gold, fee, balances, rates, i)

            # make sure we buy all the needed gold first before trading it for
            # other coins, otherwise we risk getting into negative territory
            ops_ = sorted(ops_, key=lambda o: o.op == SELL_OP)
            ops.append((i, ops_))

            # adjust balances for next iteration
            balances = self.apply_ops(gold, balances, ops_)

            # log wealth change
            gold_total = self.get_gold_total(balances, rates, i)
            print('%.3f %s total (%s)' % (gold_total, gold, balances))
        return ops, balances


class CRPStrategy(Strategy):
    def get_weights(self, targets, weights, gold, balances, rates, i):
        # validate input before proceeding
        total_weight = 0
        for target, weight in zip(targets, weights):
            total_weight += weight
        # todo: revisit the rounding workaround
        if round(total_weight, 5) != round(1.0):
            raise RuntimeError("error: weights don't add up to 1")

        return weights


class NoopStrategy(Strategy):
    def get_weights(self, targets, weights, gold, balances, rates, i):
        return weights

    def get_ops(self, targets, weights, gold, fee, balances, rates, i):
        return []


class PAMRStrategy(Strategy):

    # this assumes https://github.com/booxter/olpsR variant of olpsR installed

    def get_weights(self, targets, weights, gold, balances, rates, i):

        gold_total = self.get_gold_total(balances, rates, i)
        currencies = sorted(set(balances.keys()) | set(targets))

        # prepare arguments
        returns = [
            rates[cur][i] / rates[cur][i - 1]
            for cur in currencies
        ]
        rets = robjects.FloatVector(returns)

        bi = [
            balances[cur] * rates[cur][i] / gold_total
            for cur in currencies
        ]
        biv = robjects.FloatVector(bi)

        olpsR = importr("olpsR")
        weights = olpsR.alg_PAMR(biv, rets)
        weights = list(weights)

        # make sure they all add up to 1.0
        gold_idx = currencies.index(gold)
        weights[gold_idx] = (
            1.0 - sum(weights[:gold_idx] + weights[gold_idx + 1:]))

        return weights

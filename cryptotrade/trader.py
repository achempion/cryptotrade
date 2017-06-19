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

import numpy as np
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
    def get_targets(self, targets, gold, balances, rates, i):
        pass

    @staticmethod
    def get_gold_total(balances, rates, i):
        return sum(
            balances[currency] * rates[currency][i]
            for currency in balances)

    def get_ops(self, targets, gold, fee, balances, rates, i):
        ops = []
        balances = balances.copy()

        gold_total = self.get_gold_total(balances, rates, i)
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
    def trade(self, targets, gold, fee, balances, rates):
        ops = []
        balances = balances.copy()
        for i in range(len(rates[gold])):
            # calculate new targets
            targets = self.get_targets(targets, gold, balances, rates, i)
            assert \
                sum(targets.values()) == 1.0, "new targets don't add up to 1.0"

            # produce buy/sell operations based on current balance and targets
            ops_ = self.get_ops(targets, gold, fee, balances, rates, i)

            # make sure we buy all the needed gold first before trading it for
            # other coins, otherwise we risk getting into negative territory
            ops_ = sorted(ops_, key=lambda o: o.op == SELL_OP)
            ops.append((i, ops_))

            # adjust balances for next iteration
            balances = self.apply_ops(gold, balances, ops_)
        return ops, balances


class CRPStrategy(Strategy):
    def get_targets(self, targets, gold, balances, rates, i):
        return targets


class NoopStrategy(Strategy):
    def get_targets(self, targets, gold, balances, rates, i):
        return targets

    def get_ops(self, targets, gold, fee, balances, rates, i):
        return []


class PAMRStrategy(Strategy):

    def __init__(self, *args, **kwargs):
        super(PAMRStrategy, self).__init__(*args, **kwargs)
        self.prev_bt = None

    @staticmethod
    def multiply(v1, v2):
        assert set(v1.keys()) == set(v2.keys()), 'vector keys must be the same'
        return sum([
            v1[currency] * v2[currency]
            for currency in v1
        ])

    @staticmethod
    def subtract(v1, v2):
        assert set(v1.keys()) == set(v2.keys()), 'vector keys must be the same'
        return {
            currency: (v1[currency] - v2[currency])
            for currency in v1
        }

    def get_targets(self, targets, gold, balances, rates, i):
        balances = balances.copy()
        gold_total = self.get_gold_total(balances, rates, i)

        # Initialize b1 based on existing balances
        prev_bt = self.prev_bt
        if prev_bt is None:
            prev_bt = {
                currency: rates[currency][i] * amount / gold_total
                for currency, amount in balances.items()
            }
            for k in targets:
                if k not in prev_bt:
                    prev_bt[k] = 0.0

        # Calculate stock price relatives
        if i == 0:
            xt_ = 1.0
            xt = {currency: xt_ for currency in targets}
        else:
            prev_gold_total = self.get_gold_total(balances, rates, i - 1)
            xt = {
                currency: rates[currency][i] / rates[currency][i - 1]
                for currency in targets
            }
            xt[gold] = 1.0
            xt_ = sum(v for v in xt.values()) / len(xt)

        # Suffer loss:
        eps = 1.0
        suffer_loss = max(0, self.multiply(prev_bt, xt) - eps)

        # Set parameters (unmodified PAMR)
        xdiff = self.subtract(xt, {currency: xt_ for currency in xt})
        xdiff = {currency: abs(diff) for currency, diff in xdiff.items()}
        xdiff2 = self.multiply(xdiff, xdiff)
        if xdiff2:
            tao = min(10, suffer_loss / xdiff2)

            # Update portfolio
            bt_tmp = self.subtract(
                prev_bt,
                {k: v * tao for k, v in xdiff.items()})

            # Normalize portfolio
            currencies = sorted(bt_tmp.keys())
            to_project = [bt_tmp[cur] for cur in currencies]
            res = euclidean_proj_simplex(to_project)

            next_bt = {}
            for v, cur in zip(res, currencies):
                next_bt[cur] = v

            # make sure they all add up to 1
            next_bt[gold] = (
                1.0 - sum(v for k, v in next_bt.items() if k != gold))
        else:
            next_bt = prev_bt

        self.prev_bt = next_bt
        return next_bt


# somewhere from internet, to replace with something more safe proof
def euclidean_proj_simplex(v, s=1):
    """ Compute the Euclidean projection on a positive simplex

    Solves the optimisation problem (using the algorithm from [1]):

        min_w 0.5 * || w - v ||_2^2 , s.t. \sum_i w_i = s, w_i >= 0

    Parameters
    ----------
    v: (n,) numpy array,
       n-dimensional vector to project

    s: int, optional, default: 1,
       radius of the simplex

    Returns
    -------
    w: (n,) numpy array,
       Euclidean projection of v on the simplex

    Notes
    -----
    The complexity of this algorithm is in O(n log(n)) as it involves sorting
    v.  Better alternatives exist for high-dimensional sparse vectors (cf. [1])
    However, this implementation still easily scales to millions of dimensions.

    References
    ----------
    [1] Efficient Projections onto the .1-Ball for Learning in High Dimensions
        John Duchi, Shai Shalev-Shwartz, Yoram Singer, and Tushar Chandra.
        International Conference on Machine Learning (ICML 2008)
        http://www.cs.berkeley.edu/~jduchi/projects/DuchiSiShCh08.pdf
    """
    v = np.asarray(v)
    assert s > 0, "Radius s must be strictly positive (%d <= 0)" % s
    n, = v.shape  # will raise ValueError if v is not 1-D
    # check if we are already on the simplex
    if v.sum() == s and np.alltrue(v >= 0):
        # best projection: itself!
        return v
    # get the array of cumulative sums of a sorted (decreasing) copy of v
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u)
    # get the number of > 0 components of the optimal solution
    rho = np.nonzero(u * np.arange(1, n + 1) > (cssv - s))[0][-1]
    # compute the Lagrange multiplier associated to the simplex constraint
    theta = (cssv[rho] - s) / (rho + 1.0)
    # compute the projection by thresholding v using theta
    w = (v - theta).clip(min=0)
    return w

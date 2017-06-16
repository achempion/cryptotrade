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

import configparser


_SUPPORTED_SECTIONS = ('core', 'poloniex',)


class TargetNotFound(Exception):
    message = "No target found in config file."


class UnbalancedTarget(Exception):
    message = "Targets don't add up to 1."


# format of target string is: 'BTC=0.XX;ETH=0.XX;...'
def _extract_target(conf):
    res = {}
    target = conf.get('core', {}).get('target', '')
    if not target:
        raise TargetNotFound
    for subtarget in target.split(';'):
        currency, t = subtarget.split('=')
        res[currency] = float(t)
    if sum(v for v in res.values()) != 1.0:
        raise UnbalancedTarget
    return res


def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    # filter out unknown sections
    res = {
        section: dict(config[section])
        for section in _SUPPORTED_SECTIONS
        if section in config and config[section]
    }
    res['core']['target'] = _extract_target(res)
    return res

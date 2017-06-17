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

import logging
import os
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager

from cryptotrade import config
from cryptotrade import version


LOG = logging.getLogger(__name__)


# todo: maybe move somewhere else
CONFIG_FILE = '.cryptotrade.conf'
CONFIG_PATH = os.path.join(os.path.expanduser('~'), CONFIG_FILE)


class CtApp(App):
    def __init__(self):
        super(CtApp, self).__init__(
            description=sys.modules[__name__].__doc__,
            version=version.get_version(),
            command_manager=CommandManager('ct.cli'),
            deferred_help=True,
            )

    def build_option_parser(self, *args, **kwargs):
        parser = super(CtApp, self).build_option_parser(*args, **kwargs)
        parser.add_argument(
            '-c',
            dest='config_file',
            metavar='FILE',
            default=CONFIG_PATH,
            help='configuration file to load (default: ~/%s)' % CONFIG_FILE)
        return parser

    def prepare_to_run_command(self, cmd):
        self.cfg = config.get_config(
            getattr(self.options, 'config_file', CONFIG_PATH))


def main(argv=sys.argv[1:]):
    app = CtApp()
    return app.run(argv)

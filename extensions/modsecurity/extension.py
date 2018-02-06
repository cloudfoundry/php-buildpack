import logging
from os import path
from build_pack_utils import utils

_log = logging.getLogger('modsecurity')

class ModsecurityConfiguration(object):
    def __init__(self, ctx):
        self._ctx = ctx
        self._log = _log
        self._init_modsecurity_paths()

    def _init_modsecurity_paths(self):
        directories = ['audit', 'crs', 'log', 'tmp', 'upload']
        for directory in directories:
            self.add_entry(directory)
            self.make_dir(directory)

    def add_entry(self, elem):
        self._ctx['MODSECURITY_{0}_DIR'.format(
            elem.upper())] = path.join(
                self._ctx['BUILD_DIR'], 'modsecurity', elem)

    def make_dir(self, elem):
        utils.safe_makedirs(
            self._ctx['MODSECURITY_{0}_DIR'.format(elem.upper())])


# Extension Methods
def configure(ctx):
    modsecurity = ModsecurityConfiguration(ctx)

def preprocess_commands(ctx):
    return ()

def service_commands(ctx):
    return {}

def service_environment(ctx):
    return {}

def compile(install):
    print('Installing Modsecurity')
    (install
        .config()
            .from_application('.bp-config/modsecurity-crs')  # noqa
            .or_from_build_pack('defaults/config/modsecurity-crs')
            .to('modsecurity/crs')
            .rewrite()
            .done())
    return 0

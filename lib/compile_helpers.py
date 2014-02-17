import os
import os.path
import logging
from build_pack_utils import FileUtil


_log = logging.getLogger('helpers')


class FakeBuilder(object):
    def __init__(self, ctx):
        self._ctx = ctx


class FakeInstaller(object):
    def __init__(self, builder, installer):
        self._installer = installer
        self.builder = builder


def setup_htdocs_if_it_doesnt_exist(ctx):
    htdocsPath = os.path.join(ctx['BUILD_DIR'], 'htdocs')
    if not os.path.exists(htdocsPath):
        fu = FileUtil(FakeBuilder(ctx), move=True)
        fu.under('BUILD_DIR')
        fu.into('htdocs')
        fu.where_name_does_not_match(
            '^%s.*$' % os.path.join(ctx['BUILD_DIR'], 'config'))
        fu.where_name_does_not_match(
            '^%s.*$' % os.path.join(ctx['BUILD_DIR'], 'lib'))
        fu.done()


def convert_php_extensions(ctx):
    _log.debug('Converting PHP extensions')
    ctx['PHP_EXTENSIONS'] = \
        "\n".join(["extension=%s.so" % ex for ex in ctx['PHP_EXTENSIONS']])
    path = '@{HOME}/php/lib/php/extensions/no-debug-non-zts-20100525'
    ctx['ZEND_EXTENSIONS'] = \
        "\n".join(['zend_extension="%s/%s.so"' % (path, ze)
                   for ze in ctx['ZEND_EXTENSIONS']])

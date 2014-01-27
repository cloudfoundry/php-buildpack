import os
import os.path
from build_pack_utils import FileUtil


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

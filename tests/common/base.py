import os
from build_pack_utils import BuildPack
from common.integration import DirectoryHelper
from common.integration import OptionsHelper


class BaseCompileApp(object):
    def setUp(self):
        self.dh = DirectoryHelper()
        (self.build_dir,
         self.cache_dir,
         self.temp_dir) = self.dh.create_bp_env(self.app_name)
        self.bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'TMPDIR': self.temp_dir
        }, '.')
        if 'BP_DEBUG' in os.environ.keys():
            self.bp._ctx['BP_DEBUG'] = True
        self.dh.copy_build_pack_to(self.bp.bp_dir)
        self.dh.register_to_delete(self.bp.bp_dir)
        self.opts = OptionsHelper(os.path.join(self.bp.bp_dir,
                                               'defaults',
                                               'options.json'))
        self.opts.set_download_url(
            'http://localhost:5000/binaries/{STACK}')

        os.environ["CF_STACK"] = "cflinuxfs2"

    def tearDown(self):
        self.dh.cleanup()

        del os.environ["CF_STACK"]

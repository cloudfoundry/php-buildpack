import shutil
import tempfile
import os.path
import json
from nose.tools import eq_
from dingus import Dingus
from dingus import patch
from build_pack_utils import utils


class TestComposer(object):

    def __init__(self):
        self.ct = utils.load_extension('extensions/composer')

    def test_composer_tool_detect(self):
        ctx =  utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir'
        })
        builder = Dingus(_ctx=ctx)
        listdir = Dingus(return_value=('composer.json',))
        with patch('os.listdir', listdir):
            ct = self.ct.ComposerTool(builder)
            assert ct.detect()
        assert listdir.calls().once()

    def test_composer_tool_install(self):
        ctx =  utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir'
        })
        builder = Dingus(_ctx=ctx)
        installer = Dingus()
        cfInstaller = Dingus()
        builder.install = Dingus(_installer=cfInstaller,
                                 return_value=installer)
        ct = self.ct.ComposerTool(builder)
        ct.install()
        eq_(2, len(builder.install.calls()))
        assert installer.modules.calls().once()
        eq_('PHP', installer.modules.calls()[0].args[0])
        call = installer.modules.calls()[0]
        assert call.return_value.calls().once()
        eq_('cli', call.return_value.calls()[0].args[0])
        assert installer.calls().once()

    def test_composer_tool_run(self):
        ctx =  utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir'
        })
        builder = Dingus(_ctx=ctx)
        old_check_output = self.ct.check_output
        co = Dingus()
        self.ct.check_output = co
        try:
            ct = self.ct.ComposerTool(builder)
            ct.run()
            eq_(2, len(builder.move.calls()))
            assert co.calls().once()
            eq_('install', co.calls()[0].args[0][2])
            eq_('--no-progress', co.calls()[0].args[0][3])
        finally:
            self.ct.check_output = old_check_output

    def test_process_commands(self):
        eq_(0, len(self.ct.preprocess_commands({})))

    def test_service_commands(self):
        eq_(0, len(self.ct.service_commands({})))

    def test_service_environment(self):
        eq_(0, len(self.ct.service_environment({})))

    def test_compile(self):
        composer = Dingus()
        composer.return_value.detect.return_value = True
        builder = Dingus()
        old_composer_tool = self.ct.ComposerTool
        self.ct.ComposerTool = composer
        try:
            self.ct.compile(builder)
            assert composer.calls().once()
            assert composer.return_value.detect.calls().once()
            assert composer.return_value.install.calls().once()
            assert composer.return_value.run.calls().once()
        finally:
            self.ct.ComposerTool = old_composer_tool

    def test_compile_detect_fails(self):
        composer = Dingus()
        composer.return_value.detect.return_value = False 
        builder = Dingus()
        old_composer_tool = self.ct.ComposerTool
        self.ct.ComposerTool = composer
        try:
            self.ct.compile(builder)
            assert composer.calls().once()
            assert composer.return_value.detect.calls().once()
            eq_(0, len(composer.return_value.install.calls()))
            eq_(0, len(composer.return_value.run.calls()))
        finally:
            self.ct.ComposerTool = old_composer_tool

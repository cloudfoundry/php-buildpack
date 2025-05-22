import unittest
import tempfile
import shutil
import os
import json
from build_pack_utils import utils
from unittest.mock import MagicMock
from lib.build_pack_utils import builder
from nose.tools import eq_, assert_not_in


class TestBuilderDefaultConfig(unittest.TestCase):
    def setUp(self):
        self.bp_dir = tempfile.mkdtemp()
        self.manifest_path = os.path.join(self.bp_dir, 'manifest.yml')
        self.manifest_content = """---
default_versions:
  - name: php
    version: 8.2.7
dependencies:
  - name: php
    version: 8.2.7
  - name: php
    version: 8.2.9
  - name: php
    version: 8.1.20
  - name: php
    version: 8.1.15
  - name: php
    version: 8.0.30
  - name: nginx
    version: 1.21.1
"""

        with open(self.manifest_path, 'w') as f:
            f.write(self.manifest_content)

        ctx = utils.FormattedDict({
            'BP_DIR': self.bp_dir
        })
        self.builder = MagicMock(_ctx=ctx)
        self.configurer = builder.Configurer(self.builder)

    def tearDown(self):
        shutil.rmtree(self.bp_dir)

    def test_default_config_sets_php_default_and_stream_latest(self):
        self.configurer.default_config()
        injected = self.builder._ctx

        eq_(injected.get('PHP_DEFAULT'), '8.2.7')
        eq_(injected.get('PHP_82_LATEST'), '8.2.9')
        eq_(injected.get('PHP_81_LATEST'), '8.1.20')
        eq_(injected.get('PHP_80_LATEST'), '8.0.30')

        assert_not_in('PHP_83_LATEST', injected)

    def test_default_config_ignores_non_php_dependencies(self):
        self.configurer.default_config()
        assert_not_in('NGINX_LATEST', self.builder._ctx)

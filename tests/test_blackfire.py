import os
import os.path
import tempfile
import shutil
import json
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils
from common.integration import ErrorHelper
from common.components import BuildPackAssertHelper
from common.components import HttpdAssertHelper
from common.components import PhpAssertHelper
from common.components import NoWebServerAssertHelper
from common.components import BlackfireAssertHelper
from common.components import HhvmAssertHelper
from common.components import DownloadAssertHelper
from common.base import BaseCompileApp


blackfire = utils.load_extension('extensions/blackfire')


class TestBlackfire(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp(prefix='build-')
        self.php_dir = os.path.join(self.build_dir, 'php', 'etc')
        os.makedirs(self.php_dir)
        shutil.copy('defaults/config/php/5.4.x/php.ini', self.php_dir)
        shutil.copy('defaults/config/php/5.4.x/php-fpm.conf', self.php_dir)

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

    def testShouldCompileNotSet(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.35'
        })
        ext = blackfire.BlackfireExtension(ctx)
        eq_(False, ext._should_compile())

    def testShouldCompileManualSet(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.35',
            'BLACKFIRE_SERVER_ID': 'TEST_SERVER_ID',
            'BLACKFIRE_SERVER_TOKEN': 'TEST_SERVER_TOKEN'
        })
        ext = blackfire.BlackfireExtension(ctx)
        eq_(True, ext._should_compile())
        eq_('TEST_SERVER_ID', ext.server_id)
        eq_('TEST_SERVER_TOKEN', ext.server_token)

    def testShouldCompileServiceSet(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.35',
            'VCAP_SERVICES': {
                'blackfire': [{
                    'credentials': {
                        'serverId': 'TEST_SERVER_ID',
                        'serverToken': 'TEST_SERVER_TOKEN'
                    },
                    'label': 'blackfire'
                }]
            }
        })
        ext = blackfire.BlackfireExtension(ctx)
        eq_(True, ext._should_compile())
        eq_('TEST_SERVER_ID', ext.server_id)
        eq_('TEST_SERVER_TOKEN', ext.server_token)

    def testShouldCompileServiveAndManuelSet(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.35',
            'VCAP_SERVICES': {
                'blackfire': [{
                    'credentials': {
                        'serverId': 'TEST_SERVICE_SERVER_ID',
                        'serverToken': 'TEST_SERVICE_SERVER_TOKEN'
                    },
                    'label': 'blackfire'
                }]  
            },
            'BLACKFIRE_SERVER_ID': 'TEST_MANUAL_SERVER_ID',
            'BLACKFIRE_SERVER_TOKEN': 'TEST_MANUAL_SERVER_TOKEN',
        })
        ext = blackfire.BlackfireExtension(ctx)
        eq_(True, ext._should_compile())
        eq_('TEST_MANUAL_SERVER_ID', ext.server_id)
        eq_('TEST_MANUAL_SERVER_TOKEN', ext.server_token)

    def testUpdatePhpIni(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.35',
            'BLACKFIRE_SERVER_ID': 'TEST_SERVER_ID',
            'BLACKFIRE_SERVER_TOKEN': 'TEST_SERVER_TOKEN'
        })
        ext = blackfire.BlackfireExtension(ctx)
        ext._should_compile()
        ext._update_php_ini()
        with open(os.path.join(self.php_dir, 'php.ini'), 'rt') as php_ini:
            lines = php_ini.readlines()
        eq_(True, lines.index('[blackfire]\n') >= 0)
        eq_(True, lines.index('blackfire.server_id=TEST_SERVER_ID\n') > 0)
        eq_(True, lines.index('blackfire.server_token=TEST_SERVER_TOKEN\n') > 0)
        
    def testWriteAgentConfig(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.35',
            'BLACKFIRE_SERVER_ID': 'TEST_SERVER_ID',
            'BLACKFIRE_SERVER_TOKEN': 'TEST_SERVER_TOKEN'
        })
        ext = blackfire.BlackfireExtension(ctx)
        agent_config_path = os.path.join(self.build_dir, 'blackfire', 'agent', 'conf.ini')
        ext._should_compile()
        ext._write_agent_configuration(agent_config_path)
        with open(agent_config_path, 'rt') as agent_config:
            lines = agent_config.readlines()
        eq_(True, lines.index('[blackfire]\n') >= 0)
        eq_(True, lines.index('server-id=e92fc80d-dc52-4cfb-8f4c-a8db940706f8\n') >= 0)
        eq_(True, lines.index('server-token=101af42ab9afcd468a3d3e9f87565008b21262b6a3d7f50812d52c911ba3d698\n') >= 0)

class TestCompileBlackfireWithPHP(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-1'

    def setUp(self):
        BaseCompileApp.setUp(self)
        os.environ['BLACKFIRE_SERVER_ID'] = 'TEST_SERVER_ID'
        os.environ['BLACKFIRE_SERVER_TOKEN'] = 'TEST_SERVER_TOKEN'
        os.environ['VCAP_APPLICATION'] = json.dumps({
            'name': 'app-name-1'
        })

    def test_compile_php_with_blackfire(self):
        bp = BuildPackAssertHelper()
        blackfire = BlackfireAssertHelper()
        self.opts.set_web_server('httpd')
        output = ErrorHelper().compile(self.bp)
        blackfire.assert_contents_of_procs_file(self.build_dir)
        blackfire.assert_files_installed(self.build_dir)

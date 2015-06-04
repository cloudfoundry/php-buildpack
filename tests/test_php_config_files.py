import os


class TestPHPConfigFiles(object):
    def test_disables_expose_php(self):
        php_config_dir = 'defaults/config/php'
        for version_dir in os.listdir(php_config_dir):
            ini_file = os.path.join(php_config_dir, version_dir, 'php.ini')
            with open(ini_file) as f:
                s = f.read()
                assert 'expose_php = Off' in s

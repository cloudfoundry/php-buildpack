"""NewRelic Extension

Downloads, installs and configures the NewRelic agent for PHP
"""
import os
import os.path
import logging


_log = logging.getLogger('newrelic')


DEFAULTS = {
    'NEWRELIC_HOST': 'download.newrelic.com',
    'NEWRELIC_VERSION': '4.5.5.38',
    'NEWRELIC_PACKAGE': 'newrelic-php5-{NEWRELIC_VERSION}-linux.tar.gz',
    'NEWRELIC_DOWNLOAD_URL': '{DOWNLOAD_URL}/newrelic/{NEWRELIC_PACKAGE}',
    #'NEWRELIC_DOWNLOAD_URL': 'https://{NEWRELIC_HOST}/php_agent/'
    #                         'archive/{NEWRELIC_VERSION}/{NEWRELIC_PACKAGE}',
    'NEWRELIC_HASH_DOWNLOAD_URL': '{DOWNLOAD_URL}/newrelic/'
                                  '{NEWRELIC_PACKAGE}.{CACHE_HASH_ALGORITHM}',
    'NEWRELIC_STRIP': True
}


class NewRelicInstaller(object):
    def __init__(self, ctx):
        self._log = _log
        ctx.update(DEFAULTS)
        self._ctx = ctx
        if self.should_install():
            self._log.info("Initializing")
            self.php_ini_path = os.path.join(self._ctx['BUILD_DIR'],
                                             'php', 'etc', 'php.ini')
            self._php_extn_dir = self._find_php_extn_dir()
            self._php_api, self._php_zts = self._parse_php_api()
            self._php_arch = ctx.get('NEWRELIC_ARCH', 'x64')
            self._log.debug("PHP API [%s] Arch [%s]", 
                            self._php_api, self._php_arch)
            self.newrelic_so = os.path.join(
                '@{HOME}', 'newrelic',
                'agent', self._php_arch,
                'newrelic-%s%s.so' % (self._php_api,
                                      (self._php_zts and 'zts' or '')))
            self._log.debug("PHP Extension [%s]", self.newrelic_so)
            self.app_name = ctx['VCAP_APPLICATION']['name']
            self._log.debug("App Name [%s]", self.app_name)
            self.log_path = os.path.join('@{HOME}', '..', 'logs',
                                         'newrelic-daemon.log')
            self.daemon_path = os.path.join(
                '@{HOME}', 'newrelic', 'daemon',
                'newrelic-daemon.%s' % self._php_arch)
            self._log.debug("Daemon [%s]", self.daemon_path)
            self.socket_path = os.path.join('@{HOME}', 'newrelic',
                                            'daemon.sock')
            self._log.debug("Socket [%s]", self.socket_path)
            self.pid_path = os.path.join('@{HOME}', 'newrelic',
                                         'daemon.pid')
            self._log.debug("Pid File [%s]", self.pid_path)

    def _find_php_extn_dir(self):
        with open(self.php_ini_path, 'rt') as php_ini:
            for line in php_ini.readlines():
                if line.startswith('extension_dir'):
                    (key, val) = line.strip().split(' = ')
                    return val.strip('"')

    def _parse_php_api(self):
        tmp = os.path.basename(self._php_extn_dir)
        php_api = tmp.split('-')[-1]
        php_zts = (tmp.find('non-zts') == -1)
        return php_api, php_zts

    def should_install(self):
        return 'NEWRELIC_LICENSE' in self._ctx.keys()

    def modify_php_ini(self):
        with open(self.php_ini_path, 'rt') as php_ini:
            lines = php_ini.readlines()
        extns = [line for line in lines if line.startswith('extension=')]
        if len(extns) > 0:
            pos = lines.index(extns[-1]) + 1
        else:
            pos = lines.index('#{PHP_EXTENSIONS}\n') + 1
        lines.insert(pos, 'extension=%s\n' % self.newrelic_so)
        lines.append('\n')
        lines.append('[newrelic]\n')
        lines.append('newrelic.license=%s\n' % self._ctx['NEWRELIC_LICENSE'])
        lines.append('newrelic.appname=%s\n' % self.app_name)
        lines.append('newrelic.daemon.logfile=%s\n' % self.log_path)
        lines.append('newrelic.daemon.location=%s\n' % self.daemon_path)
        lines.append('newrelic.daemon.port=%s\n' % self.socket_path)
        lines.append('newrelic.daemon.pidfile=%s\n' % self.pid_path)
        with open(self.php_ini_path, 'wt') as php_ini:
            for line in lines:
                php_ini.write(line)


# Extension Methods
def preprocess_commands(ctx):
    return ()


def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    newrelic = NewRelicInstaller(install.builder._ctx)
    if newrelic.should_install():
        _log.info("Installing NewRelic")
        install.package('NEWRELIC')
        _log.info("Configuring NewRelic in php.ini")
        newrelic.modify_php_ini()
        _log.info("NewRelic Installed.")
    return 0

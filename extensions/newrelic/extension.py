# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""NewRelic Extension

Downloads, installs and configures the NewRelic agent for PHP
"""
import os
import os.path
import logging


_log = logging.getLogger('newrelic')


DEFAULTS = {
    'NEWRELIC_HOST': 'download.newrelic.com',
    'NEWRELIC_VERSION': '4.20.2.95',
    'NEWRELIC_PACKAGE': 'newrelic-php5-{NEWRELIC_VERSION}-linux.tar.gz',
    'NEWRELIC_DOWNLOAD_URL': 'https://{NEWRELIC_HOST}/php_agent/'
                             'archive/{NEWRELIC_VERSION}/{NEWRELIC_PACKAGE}',
    'NEWRELIC_STRIP': True
}


class NewRelicInstaller(object):
    def __init__(self, ctx):
        self._log = _log
        self._ctx = ctx
        self._detected = False
        self.app_name = None
        self.license_key = None
        try:
            self._log.info("Initializing")
            if ctx['PHP_VM'] == 'php':
                self._merge_defaults()
                self._load_service_info()
                self._load_php_info()
                self._load_newrelic_info()
        except Exception:
            self._log.exception("Error installing NewRelic! "
                                "NewRelic will not be available.")

    def _merge_defaults(self):
        for key, val in DEFAULTS.iteritems():
            if key not in self._ctx:
                self._ctx[key] = val

    def _load_service_info(self):
        services = self._ctx.get('VCAP_SERVICES', {})
        services = services.get('newrelic', [])
        if len(services) == 0:
            self._log.info("NewRelic services not detected.")
        if len(services) > 1:
            self._log.warn("Multiple NewRelic services found, "
                           "credentials from first one.")
        if len(services) > 0:
            service = services[0]
            creds = service.get('credentials', {})
            self.license_key = creds.get('licenseKey', None)
            if self.license_key:
                self._log.debug("NewRelic service detected.")
                self._detected = True

    def _load_newrelic_info(self):
        vcap_app = self._ctx.get('VCAP_APPLICATION', {})
        self.app_name = vcap_app.get('name', None)
        self._log.debug("App Name [%s]", self.app_name)

        if 'NEWRELIC_LICENSE' in self._ctx.keys():
            if self._detected:
                self._log.warn("Detected a NewRelic Service & Manual Key,"
                               " using the manual key.")
            self.license_key = self._ctx['NEWRELIC_LICENSE']
            self._detected = True

        if self._detected:
            newrelic_so_name = 'newrelic-%s%s.so' % (
                self._php_api, (self._php_zts and 'zts' or ''))
            self.newrelic_so = os.path.join('@{HOME}', 'newrelic',
                                            'agent', self._php_arch,
                                            newrelic_so_name)
            self._log.debug("PHP Extension [%s]", self.newrelic_so)
            self.log_path = os.path.join('@{HOME}', 'logs',
                                         'newrelic-daemon.log')
            self._log.debug("Log Path [%s]", self.log_path)
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

    def _load_php_info(self):
        self.php_ini_path = os.path.join(self._ctx['BUILD_DIR'],
                                         'php', 'etc', 'php.ini')
        self._php_extn_dir = self._find_php_extn_dir()
        self._php_api, self._php_zts = self._parse_php_api()
        self._php_arch = self._ctx.get('NEWRELIC_ARCH', 'x64')
        self._log.debug("PHP API [%s] Arch [%s]",
                        self._php_api, self._php_arch)

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
        return self._detected

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
        lines.append('newrelic.license=%s\n' % self.license_key)
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

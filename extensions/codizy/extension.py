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
"""Codizy Extension

Downloads, installs and configures the Codizy extension for PHP
"""
import os
import os.path
import logging


_log = logging.getLogger('codizy')


DEFAULTS = {
    "CODIZY_VERSION": "1.3",
    "CODIZY_PACKAGE": "codizy-{CODIZY_VERSION}.tar.gz",
    "CODIZY_DOWNLOAD_URL": "https://www.codizy.com/download/module/{CODIZY_PACKAGE}",
    "CODIZY_STRIP": False
}



class CodizyInstaller(object):
    def __init__(self, ctx):
        self._log = _log
        self._ctx = ctx
        self._detected = False
        self.app_name = None
        try:
            self._log.info("Initializing")
            self._merge_defaults()
            self._load_service_info()
            self._load_php_info()
            self._load_codizy_info()
        except Exception:
            self._log.exception("Error installing Codizy module! "
                                "Codizy module will not be available.")

    def should_install(self):
        return self._detected and self._php_arch == 'x64' and int(self._php_api) >= 20100525

    def _merge_defaults(self):
        for key, val in DEFAULTS.iteritems():
            if key not in self._ctx:
                self._ctx[key] = val

    def _load_codizy_info(self):
        if 'CODIZY_INSTALL' in self._ctx.keys():
            self._log.info("Codizy manual install detected.")
            self._detected = True

        if self._detected:
            codizy_so_name = 'codizy-%s.so' % (self._php_api)
            self.codizy_so = os.path.join('@{HOME}', 'codizy',
                                        codizy_so_name)
            self._log.info("PHP Extension [%s]", self.codizy_so)

    def _load_php_info(self):
        self.php_ini_path = os.path.join(self._ctx['BUILD_DIR'],
                                         'php', 'etc', 'php.ini')
        self._php_extn_dir = self._find_php_extn_dir()
        self._php_api, self._php_zts = self._parse_php_api()
        self._php_arch = self._ctx.get('CODIZY_ARCH', 'x64')
        self._log.info("PHP API [%s] Arch [%s]",
                        self._php_api, self._php_arch)

    def _load_service_info(self):
        services = self._ctx.get('VCAP_SERVICES', {})
        services = services.get('codizy', [])
        if len(services) == 0:
            self._log.info("Codizy services not detected.")
        if len(services) > 1:
            self._log.warn("Multiple Codizy services found, "
                           "credentials from first one.")
        if len(services) > 0:
            self._log.info("Codizy services detected.")
            self._detected = True

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

    def modify_php_ini(self):
        with open(self.php_ini_path, 'rt') as php_ini:
            lines = php_ini.readlines()
        extns = [line for line in lines if line.startswith('extension=')]
        if len(extns) > 0:
            pos = lines.index(extns[-1]) + 1
        else:
            pos = lines.index('#{PHP_EXTENSIONS}\n') + 1
        lines.insert(pos, 'extension=%s\n' % self.codizy_so)
        lines.append('\n')
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
    codizy = CodizyInstaller(install.builder._ctx)
    # support for x64 environnement only & PHP 54/55 for now
    if codizy.should_install():
        _log.info("Installing Codizy module")
        install.package('CODIZY')
        _log.info("Configuring Codizy module in php.ini")
        codizy.modify_php_ini()
        _log.info("Codizy module Installed.")
    else:
        _log.info("Codizy in not supported on your platform")
    return 0

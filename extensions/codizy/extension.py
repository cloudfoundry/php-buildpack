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
import os
import os.path
import logging
from extension_helpers import PHPExtensionHelper


_log = logging.getLogger('codizy')


class CodizyExtension(PHPExtensionHelper):
    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)

    def _defaults(self):
        return {
            "CODIZY_DOWNLOAD_URL": "https://www.codizy.com/download/"
                                   "marketplace-codizy/{CODIZY_PACKAGE}",
            "CODIZY_VERSION": "1.1",
            "CODIZY_PACKAGE": "Codizy-codizy.tar.gz",
            "CODIZY_STRIP": True,
            "CODIZY_INSTALL": False
        }

    def _setup_codizy(self):
        self.load_config()
        lines = self._php_ini.find_lines_matching(r'auto_prepend_file =')
        if len(lines) == 0:
            self._php_ini.append_lines((
                'auto_prepend_file = '
                '@{HOME}/codizy/client/application/setup.php',))
        elif len(lines) == 1:
            cur = lines[0].split('=')[1].strip()
            if cur == '':
                self._php_ini.update_lines(
                    r'auto_prepend_file =',
                    'auto_prepend_file = '
                    '@{HOME}/codizy/client/application/setup.php')
            else:
                with open(os.path.join(self._ctx['BUILD_DIR'], 'php',
                                       'auto_prepend_file.php'), 'wt') as fp:
                    fp.write('<?php\n')
                    fp.write('    require("%s");\n' % cur.strip())
                    fp.write('    require("%s");\n' %
                             '@{HOME}/codizy/client/application/setup.php')
                    fp.write('?>')
                self._php_ini.update_lines(
                    r'auto_prepend_file =.*$',
                    'auto_prepend_file = @{HOME}/php/auto_prepend_file.php')
        self._php_ini.save(self._php_ini_path)

    def _configure(self):
        # add required zend extensions
        zend_exts = []
        zend_exts.extend(self._ctx.get('ZEND_EXTENSIONS', []))
        zend_exts.append('ioncube')
        # sort to make sure ioncube is always first
        ioncube_cmp = lambda x, y: ((x == 'ioncube') and -1 or
                                    ((y == 'ioncube') and 1 or 0))
        self._ctx['ZEND_EXTENSIONS'] = sorted(list(set(zend_exts)),
                                              cmp=ioncube_cmp)
        # add required extensions
        exts = []
        exts.extend(self._ctx.get('PHP_EXTENSIONS', []))
        exts.append('xhprof')
        exts.append('codizy')
        exts.append('curl')
        exts.append('gettext')
        exts.append('mbstring')
        exts.append('openssl')
        exts.append('zlib')
        self._ctx['PHP_EXTENSIONS'] = list(set(exts))

    def _should_compile(self):
        """Should we install Codizy?

        If running PHP 5.6 -> No
        If user sets CODIZY_INSTALL to True -> Yes
        If user maps a `codizy` service -> Yes
        """
        return (not self._ctx['PHP_VERSION'].startswith('5.6') and
                (self._ctx.get('CODIZY_INSTALL', False) or
                 self._ctx.get('VCAP_SERVICES', {}).get('codizy', []) != []))

    def _compile(self, install):
        _log.info('Installing Codizy %s', self._ctx['CODIZY_VERSION'])
        install.package('CODIZY')
        self._setup_codizy()


# Extension Methods
def configure(ctx):
    codizy = CodizyExtension(ctx)
    return codizy.configure()


def preprocess_commands(ctx):
    codizy = CodizyExtension(ctx)
    return codizy.preprocess_commands()


def service_commands(ctx):
    codizy = CodizyExtension(ctx)
    return codizy.service_commands()


def service_environment(ctx):
    codizy = CodizyExtension(ctx)
    return codizy.service_environment()


def compile(install):
    codizy = CodizyExtension(install.builder._ctx)
    return codizy.compile(install)

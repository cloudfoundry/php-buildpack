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
"""Composer Extension

Downloads, installs and runs Composer.
"""
import os
import os.path
import logging
from build_pack_utils import TextFileSearch
from build_pack_utils import check_output


_log = logging.getLogger('composer')


DEFAULTS = {
    'COMPOSER_HOST': 'getcomposer.org',
    'COMPOSER_VERSION': '1.0.0-alpha8',
    'COMPOSER_PACKAGE': 'composer.phar',
    'COMPOSER_DOWNLOAD_URL': 'https://{COMPOSER_HOST}/download/'
                             '{COMPOSER_VERSION}/{COMPOSER_PACKAGE}',
    'COMPOSER_HASH_URL': '{DOWNLOAD_URL}/composer/{COMPOSER_VERSION}/'
                         '{COMPOSER_PACKAGE}.{CACHE_HASH_ALGORITHM}',
    'COMPOSER_INSTALL_OPTIONS': ''
}


class ComposerTool(object):
    def __init__(self, builder):
        self._log = _log
        self._builder = builder
        self._ctx = builder._ctx
        self._merge_defaults()

    def _merge_defaults(self):
        for key, val in DEFAULTS.iteritems():
            if key not in self._ctx:
                self._ctx[key] = val

    def detect(self):
        tfs = TextFileSearch('composer.json')
        return tfs.search(self._ctx['HOME'])

    def install(self):
        self._builder.install._installer.install_binary_direct(
            self._ctx['COMPOSER_DOWNLOAD_URL'],
            self._ctx['COMPOSER_HASH_URL'],
            os.path.join(self._ctx['HOME'], 'php', 'bin'))

    def run(self):
        check_output(
            [os.path.join(self._ctx['HOME'], 'php', 'bin', 'php'),
             os.path.join(self._ctx['HOME'], 'php', 'bin', 'composer.phar'),
             'install', '--no-progress'])


# Extension Methods
def preprocess_commands(ctx):
    return ()


def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    composer = ComposerTool(install.builder)
    if composer.detect():
        composer.install()
        composer.run()
    return 0

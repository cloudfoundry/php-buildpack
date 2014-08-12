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
import sys
import logging
import json
from build_pack_utils import utils
from build_pack_utils import TextFileSearch
from build_pack_utils import stream_output


_log = logging.getLogger('composer')


DEFAULTS = {
    'COMPOSER_HOST': 'getcomposer.org',
    'COMPOSER_VERSION': '1.0.0-alpha8',
    'COMPOSER_PACKAGE': 'composer.phar',
    'COMPOSER_DOWNLOAD_URL': 'https://{COMPOSER_HOST}/download/'
                             '{COMPOSER_VERSION}/{COMPOSER_PACKAGE}',
    'COMPOSER_HASH_URL': '{DOWNLOAD_URL}/composer/{COMPOSER_VERSION}/'
                         '{COMPOSER_PACKAGE}.{CACHE_HASH_ALGORITHM}',
    'COMPOSER_INSTALL_OPTIONS': ['--no-interaction', '--no-dev'],
    'COMPOSER_VENDOR_DIR': '{BUILD_DIR}/{LIBDIR}/vendor',
    'COMPOSER_BIN_DIR': '{BUILD_DIR}/php/bin',
    'COMPOSER_CACHE_DIR': '{CACHE_DIR}/composer'
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

    @staticmethod
    def _find_composer_paths(path):
        json_path = None
        lock_path = None
        for root, dirs, files in os.walk(path):
            for f in files:
                if f == 'composer.json':
                    json_path = os.path.join(root, f)
                if f == 'composer.lock':
                    lock_path = os.path.join(root, f)
                if json_path and lock_path:
                    return (json_path, lock_path)
        return (json_path, lock_path)

    @staticmethod
    def _find_exts(require):
        exts = []
        keys = (hasattr(require, 'keys')) and require.keys() or require
        for req in keys:
            if req.startswith('ext-'):
                exts.append(req[4:])
        return exts

    @staticmethod
    def read_exts_from_composer_json(path):
        composer_json = json.load(open(path, 'r'))
        return ComposerTool._find_exts(composer_json.get('require', {}))

    @staticmethod
    def read_exts_from_composer_lock(path):
        exts = []
        composer_json = json.load(open(path, 'r'))
        # get platform exts
        exts.extend(ComposerTool._find_exts(composer_json.get('platform', {})))
        # get package exts
        for pkg in composer_json.get('packages', []):
            exts.extend(ComposerTool._find_exts(pkg.get('require', {})))
        return exts

    @staticmethod
    def read_php_version_from_composer_json(path):
        composer_json = json.load(open(path, 'r'))
        require = composer_json.get('require', {})
        return require.get('php', None)

    @staticmethod
    def read_php_version_from_composer_lock(path):
        composer_json = json.load(open(path, 'r'))
        platform = composer_json.get('platform', {})
        return platform.get('php', None)

    @staticmethod
    def pick_php_version(ctx, requested):
        selected = None
        if requested is None:
            selected = ctx['PHP_VERSION']
        elif requested == '5.3.*' or requested == '>=5.3':
            selected = ctx['PHP_54_LATEST']
        elif requested == '5.4.*' or requested == '>=5.4':
            selected = ctx['PHP_54_LATEST']
        elif requested == '5.5.*' or requested == '>=5.5':
            selected = ctx['PHP_55_LATEST']
        elif requested.startswith('5.4.'):
            selected = requested
        elif requested.startswith('5.5.'):
            selected = requested
        else:
            selected = ctx['PHP_VERSION']
        return selected

    @staticmethod
    def configure(ctx):
        exts = []
        # include any existing extensions
        exts.extend(ctx.get('PHP_EXTENSIONS', []))
        # add 'openssl' extension
        exts.append('openssl')
        # add platform extensions from composer.json & composer.lock
        (json_path, lock_path) = \
            ComposerTool._find_composer_paths(ctx['BUILD_DIR'])
        if json_path:
            exts.extend(ComposerTool.read_exts_from_composer_json(json_path))
        if lock_path:
            exts.extend(ComposerTool.read_exts_from_composer_lock(lock_path))
        # update context with new list of extensions, if composer.json exists
        if json_path or lock_path:
            if json_path:
                php_version = \
                    ComposerTool.read_php_version_from_composer_json(json_path)
            else:
                php_version = \
                    ComposerTool.read_php_version_from_composer_lock(lock_path)
            _log.debug('Composer picked PHP Version [%s]', php_version)
            ctx['PHP_VERSION'] = ComposerTool.pick_php_version(ctx,
                                                               php_version)
            ctx['PHP_EXTENSIONS'] = list(set(exts))

    def detect(self):
        (json_path, lock_path) = \
            ComposerTool._find_composer_paths(self._ctx['BUILD_DIR'])
        return (json_path is not None or lock_path is not None)

    def install(self):
        self._builder.install().modules('PHP').include_module('cli').done()
        self._builder.install()._installer.install_binary_direct(
            self._ctx['COMPOSER_DOWNLOAD_URL'],
            self._ctx['COMPOSER_HASH_URL'],
            os.path.join(self._ctx['BUILD_DIR'], 'php', 'bin'),
            extract=False)

    def run(self):
        # Move composer files out of WEBDIR
        (self._builder.move()
            .under('{BUILD_DIR}/{WEBDIR}')
            .where_name_is('composer.json')
            .into('BUILD_DIR')
         .done())
        (self._builder.move()
            .under('{BUILD_DIR}/{WEBDIR}')
            .where_name_is('composer.lock')
            .into('BUILD_DIR')
         .done())
        # Sanity Checks
        if not os.path.exists(os.path.join(self._ctx['BUILD_DIR'],
                                           'composer.lock')):
            msg = (
                'PROTIP: Include a `composer.lock` file with your '
                'application! This will make sure the exact same version '
                'of dependencies are used when you deploy to CloudFoundry.')
            self._log.warning(msg)
            print msg
        # rewrite a temp copy of php.ini for use by composer
        (self._builder.copy()
            .under('{BUILD_DIR}/php/etc')
            .where_name_is('php.ini')
            .into('TMPDIR')
         .done())
        utils.rewrite_cfgs(os.path.join(self._ctx['TMPDIR'], 'php.ini'),
                           {'TMPDIR': self._ctx['TMPDIR'],
                            'HOME': self._ctx['BUILD_DIR']},
                           delim='@')
        # Run from /tmp/staged/app
        try:
            phpPath = os.path.join(self._ctx['BUILD_DIR'], 'php', 'bin', 'php')
            phpCfg = os.path.join(self._ctx['TMPDIR'], 'php.ini')
            composerPath = os.path.join(self._ctx['BUILD_DIR'], 'php',
                                        'bin', 'composer.phar')
            composerEnv = {
                'LD_LIBRARY_PATH': os.path.join(self._ctx['BUILD_DIR'],
                                                'php', 'lib'),
                'HOME': self._ctx['BUILD_DIR'],
                'COMPOSER_VENDOR_DIR': self._ctx['COMPOSER_VENDOR_DIR'],
                'COMPOSER_BIN_DIR': self._ctx['COMPOSER_BIN_DIR'],
                'COMPOSER_CACHE_DIR': self._ctx['COMPOSER_CACHE_DIR']
            }
            composerCmd = [phpPath,
                           '-c "%s"' % phpCfg,
                           composerPath,
                           'install',
                           '--no-progress']
            composerCmd.extend(self._ctx['COMPOSER_INSTALL_OPTIONS'])
            self._log.debug("Running [%s]", ' '.join(composerCmd))
            output = stream_output(sys.stdout,
                                   ' '.join(composerCmd),
                                   env=composerEnv,
                                   cwd=self._ctx['BUILD_DIR'],
                                   shell=True)
            _log.debug('composer output [%s]', output)
        except Exception:
            _log.error("Command Failed: %s")


# Extension Methods
def configure(ctx):
    ComposerTool.configure(ctx)


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

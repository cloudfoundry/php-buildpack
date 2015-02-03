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
import re
import json
import StringIO
from build_pack_utils import utils
from build_pack_utils import stream_output
from extension_helpers import ExtensionHelper


_log = logging.getLogger('composer')


def find_composer_paths(path):
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


class ComposerConfiguration(object):
    def __init__(self, ctx):
        self._ctx = ctx
        self._log = _log
        self._init_composer_paths()

    def _init_composer_paths(self):
        (self.json_path, self.lock_path) = \
            find_composer_paths(self._ctx['BUILD_DIR'])

    def read_exts_from_path(self, path):
        exts = []
        if path:
            req_pat = re.compile(r'"require"\: \{(.*?)\}', re.DOTALL)
            ext_pat = re.compile(r'"ext-(.*?)"')
            with open(path, 'rt') as fp:
                data = fp.read()
            for req_match in req_pat.finditer(data):
                for ext_match in ext_pat.finditer(req_match.group(1)):
                    exts.append(ext_match.group(1))
        return exts

    def read_version_from_composer_json(self, key):
        composer_json = json.load(open(self.json_path, 'r'))
        require = composer_json.get('require', {})
        return require.get(key, None)

    def read_version_from_composer_lock(self, key):
        composer_json = json.load(open(self.lock_path, 'r'))
        platform = composer_json.get('platform', {})
        return platform.get(key, None)

    def pick_php_version(self, requested):
        selected = None
        if requested is None:
            selected = self._ctx['PHP_VERSION']
        elif requested == '5.3.*' or requested == '>=5.3':
            selected = self._ctx['PHP_54_LATEST']
        elif requested == '5.4.*' or requested == '>=5.4':
            selected = self._ctx['PHP_54_LATEST']
        elif requested == '5.5.*' or requested == '>=5.5':
            selected = self._ctx['PHP_55_LATEST']
        elif requested.startswith('5.4.'):
            selected = requested
        elif requested.startswith('5.5.'):
            selected = requested
        else:
            selected = self._ctx['PHP_VERSION']
        return selected

    def _read_version_from_composer(self, key):
        if self.json_path:
            return self.read_version_from_composer_json(key)

        elif self.lock_path:
            return self.read_version_from_composer_lock(key)

    def configure(self):
        if self.json_path or self.lock_path:
            exts = []
            # include any existing extensions
            exts.extend(self._ctx.get('PHP_EXTENSIONS', []))
            # add 'openssl' extension
            exts.append('openssl')
            # add platform extensions from composer.json & composer.lock
            exts.extend(self.read_exts_from_path(self.json_path))
            exts.extend(self.read_exts_from_path(self.lock_path))
            hhvm_version = self._read_version_from_composer('hhvm')
            if hhvm_version:
                self._ctx['PHP_VM'] = 'hhvm'
                self._log.debug('Composer picked HHVM Version [%s]',
                                hhvm_version)
            else:
                # update context with new list of extensions,
                # if composer.json exists
                php_version = self._read_version_from_composer('php')
                self._log.debug('Composer picked PHP Version [%s]',
                                php_version)
                self._ctx['PHP_VERSION'] = self.pick_php_version(php_version)
                self._ctx['PHP_EXTENSIONS'] = utils.unique(exts)
                self._ctx['PHP_VM'] = 'php'


class ComposerExtension(ExtensionHelper):
    def __init__(self, ctx):
        ExtensionHelper.__init__(self, ctx)
        self._log = _log
        if ctx['PHP_VM'] == 'hhvm':
            self.composer_strategy = HHVMComposerStrategy(ctx)
        else:
            self.composer_strategy = PHPComposerStrategy(ctx)

    def _defaults(self):
        return {
            'COMPOSER_VERSION': '1.0.0-alpha8',
            'COMPOSER_PACKAGE': 'composer.phar',
            'COMPOSER_DOWNLOAD_URL': '{DOWNLOAD_URL}/composer/'
                                     '{COMPOSER_VERSION}/{COMPOSER_PACKAGE}',
            'COMPOSER_HASH_URL': '{DOWNLOAD_URL}/composer/{COMPOSER_VERSION}/'
                                 '{COMPOSER_PACKAGE}.{CACHE_HASH_ALGORITHM}',
            'COMPOSER_INSTALL_OPTIONS': ['--no-interaction', '--no-dev'],
            'COMPOSER_VENDOR_DIR': '{BUILD_DIR}/{LIBDIR}/vendor',
            'COMPOSER_BIN_DIR': '{BUILD_DIR}/php/bin',
            'COMPOSER_CACHE_DIR': '{CACHE_DIR}/composer'
        }

    def _should_compile(self):
        (json_path, lock_path) = \
            find_composer_paths(self._ctx['BUILD_DIR'])
        return (json_path is not None or lock_path is not None)

    def binary_path(self):
        return self.composer_strategy.binary_path()

    def ld_library_path(self):
        return self.composer_strategy.ld_library_path()

    def _compile(self, install):
        self._builder = install.builder
        self.move_local_vendor_folder()
        self.install()
        self.run()

    def move_local_vendor_folder(self):
        vendor_path = os.path.join(self._ctx['BUILD_DIR'],
                                   self._ctx['WEBDIR'],
                                   'vendor')
        if os.path.exists(vendor_path):
            self._log.debug("Vendor [%s] exists, moving to LIBDIR", vendor_path)
            (self._builder.move()
                .under('{BUILD_DIR}/{WEBDIR}')
                .into('{BUILD_DIR}/{LIBDIR}')
                .where_name_matches('^%s/.*$' % vendor_path)
                .done())

    def install(self):
        self._builder.install().modules('PHP').include_module('cli').done()
        self._builder.install()._installer.install_binary_direct(
            self._ctx['COMPOSER_DOWNLOAD_URL'],
            self._ctx['COMPOSER_HASH_URL'],
            os.path.join(self._ctx['BUILD_DIR'], 'php', 'bin'),
            extract=False)

    def _build_composer_environment(self):
        env = {}
        for key in os.environ.keys():
            val = self._ctx.get(key, '')
            if type(val) != str:
                env[key] = json.dumps(val)
            else:
                env[key] = self._ctx.get(key, '')

        # add basic composer vars
        env['COMPOSER_VENDOR_DIR'] = self._ctx['COMPOSER_VENDOR_DIR']
        env['COMPOSER_BIN_DIR'] = self._ctx['COMPOSER_BIN_DIR']
        env['COMPOSER_CACHE_DIR'] = self._ctx['COMPOSER_CACHE_DIR']

        # prevent key system variables from being overridden
        env['LD_LIBRARY_PATH'] = self.ld_library_path()
        env['PHPRC'] = self._ctx['TMPDIR']
        return env

    def _github_oauth_token_is_valid(self, candidate_oauth_token):
        stringio_writer = StringIO.StringIO()

        curl_command = 'curl -H "Authorization: token %s" https://api.github.com/rate_limit' % candidate_oauth_token

        stream_output(stringio_writer,
                      curl_command,
                      env=os.environ,
                      cwd=self._ctx['BUILD_DIR'],
                      shell=True)

        github_response = stringio_writer.getvalue()

        github_response_json = json.loads(github_response)
        return 'resources' in github_response_json

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
        self.composer_strategy.write_config(self._builder)
        # Run from /tmp/staged/app
        try:
            phpPath = self.binary_path()
            composerPath = os.path.join(self._ctx['BUILD_DIR'], 'php',
                                        'bin', 'composer.phar')

            if os.getenv('COMPOSER_GITHUB_OAUTH_TOKEN', False):
                github_oauth_token = os.getenv('COMPOSER_GITHUB_OAUTH_TOKEN')
                if self._github_oauth_token_is_valid(github_oauth_token):
                    print('-----> Using custom GitHub OAuth token in $COMPOSER_GITHUB_OAUTH_TOKEN')
                    composer_oauth_config_command = [phpPath,
                       composerPath,
                       'config',
                       '-g',
                       'github-oauth.github.com',
                       '"%s"' % github_oauth_token]
                    output = stream_output(sys.stdout,
                                           ' '.join(composer_oauth_config_command),
                                           env=self._build_composer_environment(),
                                           cwd=self._ctx['BUILD_DIR'],
                                           shell=True)

            composer_install_command = [phpPath,
                           composerPath,
                           'install',
                           '--no-progress']
            composer_install_command.extend(self._ctx['COMPOSER_INSTALL_OPTIONS'])
            self._log.debug("Running [%s]", ' '.join(composer_install_command))
            self._log.debug("ENV IS: %s",
                            '\n'.join(["%s=%s (%s)" % (key, val, type(val))
                                       for (key, val) in self._build_composer_environment().iteritems()]))
            output = stream_output(sys.stdout,
                                   ' '.join(composer_install_command),
                                   env=self._build_composer_environment(),
                                   cwd=self._ctx['BUILD_DIR'],
                                   shell=True)
            _log.debug('composer output [%s]', output)
        except:
            print "-----> Composer command failed"
            _log.exception("Composer failed")
            raise


class HHVMComposerStrategy(object):
    def __init__(self, ctx):
        self._ctx = ctx

    def binary_path(self):
        return os.path.join(
            self._ctx['BUILD_DIR'], 'hhvm', 'usr', 'bin', 'hhvm')

    def write_config(self, builder):
        pass

    def ld_library_path(self):
        return os.path.join(
            self._ctx['BUILD_DIR'], 'hhvm', 'usr', 'lib', 'hhvm')


class PHPComposerStrategy(object):
    def __init__(self, ctx):
        self._ctx = ctx

    def binary_path(self):
        return os.path.join(
            self._ctx['BUILD_DIR'], 'php', 'bin', 'php')

    def write_config(self, builder):
        # rewrite a temp copy of php.ini for use by composer
        (builder.copy()
            .under('{BUILD_DIR}/php/etc')
            .where_name_is('php.ini')
            .into('TMPDIR')
         .done())
        utils.rewrite_cfgs(os.path.join(self._ctx['TMPDIR'], 'php.ini'),
                           {'TMPDIR': self._ctx['TMPDIR'],
                            'HOME': self._ctx['BUILD_DIR']},
                           delim='@')

    def ld_library_path(self):
        return os.path.join(
            self._ctx['BUILD_DIR'], 'php', 'lib')



# Extension Methods
def configure(ctx):
    config = ComposerConfiguration(ctx)
    config.configure()


def preprocess_commands(ctx):
    composer = ComposerExtension(ctx)
    return composer.preprocess_commands()


def service_commands(ctx):
    composer = ComposerExtension(ctx)
    return composer.service_commands()


def service_environment(ctx):
    composer = ComposerExtension(ctx)
    return composer.service_environment()


def compile(install):
    composer = ComposerExtension(install.builder._ctx)
    return composer.compile(install)

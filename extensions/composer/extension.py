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


def find_composer_paths(ctx):
    build_dir = ctx['BUILD_DIR']
    webdir = ctx['WEBDIR']

    json_path = None
    lock_path = None
    json_paths = [
        os.path.join(build_dir, 'composer.json'),
        os.path.join(build_dir, webdir, 'composer.json')
    ]

    lock_paths = [
        os.path.join(build_dir, 'composer.lock'),
        os.path.join(build_dir, webdir, 'composer.lock')
    ]

    env_path = os.getenv('COMPOSER_PATH')
    if env_path is not None:
        json_paths = json_paths + [
            os.path.join(build_dir, env_path, 'composer.json'),
            os.path.join(build_dir, webdir, env_path, 'composer.json')
        ]

        lock_paths = lock_paths + [
            os.path.join(build_dir, env_path, 'composer.lock'),
            os.path.join(build_dir, webdir, env_path, 'composer.lock')
        ]

    for path in json_paths:
        if os.path.exists(path):
            json_path = path
    for path in lock_paths:
        if os.path.exists(path):
            lock_path = path

    return (json_path, lock_path)


class ComposerConfiguration(object):
    def __init__(self, ctx):
        self._ctx = ctx
        self._log = _log
        self._init_composer_paths()

    def _init_composer_paths(self):
        (self.json_path, self.lock_path) = \
            find_composer_paths(self._ctx)

    def read_exts_from_path(self, path):
        exts = []
        if path:
            req_pat = re.compile(r'"require"\s?\:\s?\{(.*?)\}', re.DOTALL)
            ext_pat = re.compile(r'"ext-(.*?)"')
            with open(path, 'rt') as fp:
                data = fp.read()
            for req_match in req_pat.finditer(data):
                for ext_match in ext_pat.finditer(req_match.group(1)):
                    exts.append(ext_match.group(1))
        return exts

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
        elif requested == '5.6.*' or requested == '>=5.6':
            selected = self._ctx['PHP_56_LATEST']
        elif requested.startswith('5.4.'):
            selected = requested
        elif requested.startswith('5.5.'):
            selected = requested
        elif requested.startswith('5.6.'):
            selected = requested
        else:
            selected = self._ctx['PHP_VERSION']
        return selected

    def read_version_from_composer(self, key):
        (json_path, lock_path) = find_composer_paths(self._ctx)
        if json_path is not None:
            composer = json.load(open(json_path, 'r'))
            require = composer.get('require', {})
            return require.get(key, None)
        if lock_path is not None:
            composer = json.load(open(lock_path, 'r'))
            platform = composer.get('platform', {})
            return platform.get(key, None)
        return None

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
            hhvm_version = self.read_version_from_composer('hhvm')
            if hhvm_version:
                self._ctx['PHP_VM'] = 'hhvm'
                self._log.debug('Composer picked HHVM Version [%s]',
                                hhvm_version)
            else:
                # update context with new list of extensions,
                # if composer.json exists
                php_version = self.read_version_from_composer('php')
                self._log.debug('Composer picked PHP Version [%s]',
                                php_version)
                self._ctx['PHP_VERSION'] = self.pick_php_version(php_version)
                self._ctx['PHP_EXTENSIONS'] = utils.unique(exts)
                self._ctx['PHP_VM'] = 'php'


class ComposerExtension(ExtensionHelper):
    def __init__(self, ctx):
        ExtensionHelper.__init__(self, ctx)
        self._log = _log

    def _defaults(self):
        return {
            'COMPOSER_VERSION': '1.0.0-alpha10',
            'COMPOSER_PACKAGE': 'composer.phar',
            'COMPOSER_DOWNLOAD_URL': '/composer/'
                                     '{COMPOSER_VERSION}/{COMPOSER_PACKAGE}',
            'COMPOSER_INSTALL_OPTIONS': ['--no-interaction', '--no-dev'],
            'COMPOSER_VENDOR_DIR': '{BUILD_DIR}/{LIBDIR}/vendor',
            'COMPOSER_BIN_DIR': '{BUILD_DIR}/php/bin',
            'COMPOSER_CACHE_DIR': '{CACHE_DIR}/composer'
        }

    def _should_compile(self):
        (json_path, lock_path) = \
            find_composer_paths(self._ctx)
        return (json_path is not None or lock_path is not None)

    def _compile(self, install):
        self._builder = install.builder
        self.composer_runner = ComposerCommandRunner(self._ctx, self._builder)
        self.move_local_vendor_folder()
        self.install()
        self.run()

    def move_local_vendor_folder(self):
        vendor_path = os.path.join(self._ctx['BUILD_DIR'],
                                   self._ctx['WEBDIR'],
                                   'vendor')
        if os.path.exists(vendor_path):
            self._log.debug("Vendor [%s] exists, moving to LIBDIR",
                            vendor_path)
            (self._builder.move()
                .under('{BUILD_DIR}/{WEBDIR}')
                .into('{BUILD_DIR}/{LIBDIR}')
                .where_name_matches('^%s/.*$' % vendor_path)
                .done())

    def install(self):
        self._builder.install().package('PHP').done()
        if self._ctx['COMPOSER_VERSION'] == 'latest':
            dependencies_path = os.path.join(self._ctx['BP_DIR'],
                                             'dependencies')
            if os.path.exists(dependencies_path):
                raise RuntimeError('"COMPOSER_VERSION": "latest" ' \
                    'is not supported in the cached buildpack. Please vendor your preferred version of composer with your app, or use the provided default composer version.')

            self._ctx['COMPOSER_DOWNLOAD_URL'] = \
                'https://getcomposer.org/composer.phar'
            self._builder.install()._installer.install_binary_direct(
                self._ctx['COMPOSER_DOWNLOAD_URL'], None,
                os.path.join(self._ctx['BUILD_DIR'], 'php', 'bin'),
                extract=False)
        else:
            self._builder.install()._installer._install_binary_from_manifest(
                self._ctx['COMPOSER_DOWNLOAD_URL'],
                os.path.join(self._ctx['BUILD_DIR'], 'php', 'bin'),
                extract=False)

    def _github_oauth_token_is_valid(self, candidate_oauth_token):
        stringio_writer = StringIO.StringIO()

        curl_command = 'curl -H "Authorization: token %s" ' \
            'https://api.github.com/rate_limit' % candidate_oauth_token

        stream_output(stringio_writer,
                      curl_command,
                      env=os.environ,
                      cwd=self._ctx['BUILD_DIR'],
                      shell=True)

        github_response = stringio_writer.getvalue()

        github_response_json = json.loads(github_response)
        return 'resources' in github_response_json

    def _github_rate_exceeded(self, token_is_valid):
        stringio_writer = StringIO.StringIO()
        if token_is_valid:
            candidate_oauth_token = os.getenv('COMPOSER_GITHUB_OAUTH_TOKEN')
            curl_command = 'curl -H "Authorization: token %s" ' \
                'https://api.github.com/rate_limit' % candidate_oauth_token
        else:
            curl_command = 'curl https://api.github.com/rate_limit'

        stream_output(stringio_writer,
                      curl_command,
                      env=os.environ,
                      cwd=self._ctx['BUILD_DIR'],
                      shell=True)

        github_response = stringio_writer.getvalue()
        github_response_json = json.loads(github_response)

        rate = github_response_json['rate']
        num_remaining = rate['remaining']

        return num_remaining <= 0

    def setup_composer_github_token(self):
        github_oauth_token = os.getenv('COMPOSER_GITHUB_OAUTH_TOKEN')
        if self._github_oauth_token_is_valid(github_oauth_token):
            print('-----> Using custom GitHub OAuth token in'
                  ' $COMPOSER_GITHUB_OAUTH_TOKEN')
            self.composer_runner.run('config', '-g',
                                     'github-oauth.github.com',
                                     '"%s"' % github_oauth_token)
            return True
        else:
            print('-----> The GitHub OAuth token supplied from '
                  '$COMPOSER_GITHUB_OAUTH_TOKEN is invalid')
            return False

    def check_github_rate_exceeded(self, token_is_valid):
        if self._github_rate_exceeded(token_is_valid):
            print('-----> The GitHub api rate limit has been exceeded. '
                  'Composer will continue by downloading from source, which might result in slower downloads. '
                  'You can increase your rate limit with a GitHub OAuth token. '
                  'Please obtain a GitHub OAuth token by registering your application at '
                  'https://github.com/settings/applications/new. '
                  'Then set COMPOSER_GITHUB_OAUTH_TOKEN in your environment to the value of this token.')

    def run(self):
        # Move composer files into root directory
        (json_path, lock_path) = find_composer_paths(self._ctx)
        if json_path is not None and os.path.dirname(json_path) != self._ctx['BUILD_DIR']:
            (self._builder.move()
                .under(os.path.dirname(json_path))
                .where_name_is('composer.json')
                .into('BUILD_DIR')
             .done())
        if lock_path is not None and os.path.dirname(lock_path) != self._ctx['BUILD_DIR']:
            (self._builder.move()
                .under(os.path.dirname(lock_path))
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
        # dump composer version, if in debug mode
        if self._ctx.get('BP_DEBUG', False):
            self.composer_runner.run('-V')
        if not os.path.exists(os.path.join(self._ctx['BP_DIR'], 'dependencies')):
            token_is_valid = False
            # config composer to use github token, if provided
            if os.getenv('COMPOSER_GITHUB_OAUTH_TOKEN', False):
                token_is_valid = self.setup_composer_github_token()
            # check that the api rate limit has not been exceeded, otherwise exit
            self.check_github_rate_exceeded(token_is_valid)
        # install dependencies w/Composer
        self.composer_runner.run('install', '--no-progress',
                                 *self._ctx['COMPOSER_INSTALL_OPTIONS'])


class ComposerCommandRunner(object):
    def __init__(self, ctx, builder):
        self._log = _log
        self._ctx = ctx
        self._strategy = HHVMComposerStrategy(ctx) \
            if ctx['PHP_VM'] == 'hhvm' else PHPComposerStrategy(ctx)
        self._php_path = self._strategy.binary_path()
        self._composer_path = os.path.join(ctx['BUILD_DIR'], 'php',
                                           'bin', 'composer.phar')
        self._strategy.write_config(builder)

    def _build_composer_environment(self):
        env = {}
        for key in os.environ.keys():
            val = self._ctx.get(key, '')
            env[key] = val if type(val) == str else json.dumps(val)

        # add basic composer vars
        env['COMPOSER_VENDOR_DIR'] = self._ctx['COMPOSER_VENDOR_DIR']
        env['COMPOSER_BIN_DIR'] = self._ctx['COMPOSER_BIN_DIR']
        env['COMPOSER_CACHE_DIR'] = self._ctx['COMPOSER_CACHE_DIR']

        # prevent key system variables from being overridden
        env['LD_LIBRARY_PATH'] = self._strategy.ld_library_path()
        env['PHPRC'] = self._ctx['TMPDIR']
        env['PATH'] = ':'.join(filter(None,
                                      [env.get('PATH', ''),
                                       os.path.dirname(self._php_path)]))
        self._log.debug("ENV IS: %s",
                        '\n'.join(["%s=%s (%s)" % (key, val, type(val))
                                   for (key, val) in env.iteritems()]))
        return env

    def run(self, *args):
        try:
            cmd = [self._php_path, self._composer_path]
            cmd.extend(args)
            self._log.debug("Running command [%s]", ' '.join(cmd))
            stream_output(sys.stdout,
                          ' '.join(cmd),
                          env=self._build_composer_environment(),
                          cwd=self._ctx['BUILD_DIR'],
                          shell=True)
        except:
            print "-----> Composer command failed"
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

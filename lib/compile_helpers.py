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
from __future__ import print_function
import os
import os.path
import yaml
import logging
import glob
from build_pack_utils import FileUtil


_log = logging.getLogger('helpers')


class FakeBuilder(object):
    def __init__(self, ctx):
        self._ctx = ctx


class FakeInstaller(object):
    def __init__(self, builder, installer):
        self._installer = installer
        self.builder = builder


def setup_webdir_if_it_doesnt_exist(ctx):
    if is_web_app(ctx):
        webdirPath = os.path.join(ctx['BUILD_DIR'], ctx['WEBDIR'])
        if not os.path.exists(webdirPath):
            fu = FileUtil(FakeBuilder(ctx), move=True)
            fu.under('BUILD_DIR')
            fu.into('WEBDIR')
            fu.where_name_does_not_match(
                '^%s/.*$' % os.path.join(ctx['BUILD_DIR'], '.bp'))
            fu.where_name_does_not_match(
                '^%s/.*$' % os.path.join(ctx['BUILD_DIR'], '.extensions'))
            fu.where_name_does_not_match(
                '^%s/.*$' % os.path.join(ctx['BUILD_DIR'], '.bp-config'))
            fu.where_name_does_not_match(
                '^%s$' % os.path.join(ctx['BUILD_DIR'], 'manifest.yml'))
            fu.where_name_does_not_match(
                '^%s/.*$' % os.path.join(ctx['BUILD_DIR'], ctx['LIBDIR']))
            fu.where_name_does_not_match(
                '^%s/.*$' % os.path.join(ctx['BUILD_DIR'], '.profile.d'))
            fu.where_name_does_not_match(
                '^%s$' % os.path.join(ctx['BUILD_DIR'], '.profile'))
            fu.done()


def log_bp_version(ctx):
    version_file = os.path.join(ctx['BP_DIR'], 'VERSION')
    if os.path.exists(version_file):
        print('-------> Buildpack version %s' % open(version_file).read())


def setup_log_dir(ctx):
    os.makedirs(os.path.join(ctx['BUILD_DIR'], 'logs'))


def load_manifest(ctx):
    manifest_path = os.path.join(ctx['BP_DIR'], 'manifest.yml')
    _log.debug('Loading manifest from %s', manifest_path)
    return yaml.load(open(manifest_path))


def find_all_php_versions(dependencies):
    versions = []

    for dependency in dependencies:
        if dependency['name'] == 'php':
            versions.append(dependency['version'])

    return versions


def validate_php_version(ctx):
    if ctx['PHP_VERSION'] in ctx['ALL_PHP_VERSIONS']:
        _log.debug('App selected PHP [%s]', ctx['PHP_VERSION'])
    else:
        _log.warning('Selected version of PHP [%s] not available.  Defaulting'
                     ' to the latest version [%s]',
                     ctx['PHP_VERSION'], ctx['PHP_55_LATEST'])
        ctx['PHP_VERSION'] = ctx['PHP_55_LATEST']


def _get_supported_php_extensions(ctx):
    php_extensions = []
    php_extension_glob = os.path.join(ctx["PHP_INSTALL_PATH"], 'lib', 'php', 'extensions', 'no-debug-non-zts-*')
    php_extension_directory = glob.glob(php_extension_glob)[0]
    for root, dirs, files in os.walk(php_extension_directory):
        for f in files:
            if '.so' in f:
                php_extensions.append(f.replace('.so', ''))
    return php_extensions


def validate_php_extensions(ctx):
    filtered_extensions = []
    requested_extensions = ctx['PHP_EXTENSIONS']
    supported_extensions = _get_supported_php_extensions(ctx)

    for extension in requested_extensions:
        if extension not in supported_extensions:
            print("The extension '%s' is not provided by this buildpack." % extension, file=os.sys.stderr)
        else:
            filtered_extensions.append(extension)
    ctx['PHP_EXTENSIONS'] = filtered_extensions


def convert_php_extensions(ctx):
    _log.debug('Converting PHP extensions')
    SKIP = ('cli', 'pear', 'cgi')
    ctx['PHP_EXTENSIONS'] = \
        "\n".join(["extension=%s.so" % ex
                   for ex in ctx['PHP_EXTENSIONS'] if ex not in SKIP])
    path = ''
    ctx['ZEND_EXTENSIONS'] = \
        "\n".join(['zend_extension="%s"' % os.path.join(path, "%s.so" % ze)
                   for ze in ctx['ZEND_EXTENSIONS']])


def is_web_app(ctx):
    return ctx.get('WEB_SERVER', '') != 'none'


def find_stand_alone_app_to_run(ctx):
    app = ctx.get('APP_START_CMD', None)
    if not app:
        possible_files = ('app.php', 'main.php', 'run.php', 'start.php')
        for pf in possible_files:
            if os.path.exists(os.path.join(ctx['BUILD_DIR'], pf)):
                app = pf
                break
        if not app:
            print('Build pack could not find a PHP file to execute!')
            _log.info('Build pack could not find a file to execute.  Either '
                      'set "APP_START_CMD" or include one of these files [%s]',
                      ", ".join(possible_files))
            app = 'app.php'
    return app

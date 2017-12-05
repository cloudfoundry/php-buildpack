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
import re
import yaml
import logging
import glob
import subprocess
import platform
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
            directory_fuzzy_pattern = '^%s/.*$'
            file_exact_pattern = '^%s$'
            fu = FileUtil(FakeBuilder(ctx), move=True)
            fu.under('BUILD_DIR')
            fu.into('WEBDIR')
            fu.where_name_does_not_match(
                directory_fuzzy_pattern % os.path.join(ctx['BUILD_DIR'], '.bp'))
            fu.where_name_does_not_match(
                directory_fuzzy_pattern % os.path.join(ctx['BUILD_DIR'], '.extensions'))
            fu.where_name_does_not_match(
                directory_fuzzy_pattern % os.path.join(ctx['BUILD_DIR'], '.bp-config'))
            fu.where_name_does_not_match(
                directory_fuzzy_pattern % os.path.join(ctx['BUILD_DIR'], ctx['LIBDIR']))
            fu.where_name_does_not_match(
                file_exact_pattern % os.path.join(ctx['BUILD_DIR'], 'manifest.yml'))
            fu.where_name_does_not_match(
                directory_fuzzy_pattern % os.path.join(ctx['BUILD_DIR'], '.profile.d'))
            fu.where_name_does_not_match(
                file_exact_pattern % os.path.join(ctx['BUILD_DIR'], '.profile'))
            fu.done()


def setup_log_dir(ctx):
    logPath = os.path.join(ctx['BUILD_DIR'], 'logs')
    if not os.path.exists(logPath):
        os.makedirs(logPath)


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
                     ctx['PHP_VERSION'], ctx['PHP_56_LATEST'])

        docs_link = 'http://docs.cloudfoundry.org/buildpacks/php/gsg-php-tips.html'
        warn_invalid_php_version(ctx['PHP_VERSION'], ctx['PHP_56_LATEST'], docs_link)

        ctx['PHP_VERSION'] = ctx['PHP_56_LATEST']


def _get_supported_php_extensions(ctx):
    php_extensions = []
    php_extension_glob = os.path.join(ctx["PHP_INSTALL_PATH"], 'lib', 'php', 'extensions', 'no-debug-non-zts-*')
    php_extension_directory = glob.glob(php_extension_glob)[0]
    for root, dirs, files in os.walk(php_extension_directory):
        for f in files:
            if '.so' in f:
                php_extensions.append(f.replace('.so', ''))
    return php_extensions

def _get_compiled_modules(ctx):
    if platform.system() != 'Linux':
        return []

    compiled_modules = []
    output_to_skip = ['[PHP Modules]', '[Zend Modules]', '']

    php_binary = os.path.join(ctx["PHP_INSTALL_PATH"], 'bin', 'php')

    process = subprocess.Popen([php_binary, '-m'], stdout=subprocess.PIPE)
    exit_code = process.wait()
    output = process.stdout.read().rstrip()

    if exit_code != 0:
        _log.error("Error determining PHP compiled modules: %s", output)
        raise RuntimeError("Error determining PHP compiled modules")

    for line in output.split("\n"):
        if line not in output_to_skip:
            compiled_modules.append(line.lower())

    return compiled_modules

def validate_php_extensions(ctx):
    filtered_extensions = []
    requested_extensions = ctx['PHP_EXTENSIONS']
    supported_extensions = _get_supported_php_extensions(ctx)
    compiled_modules = _get_compiled_modules(ctx)

    for extension in requested_extensions:
        if extension in supported_extensions:
            filtered_extensions.append(extension)
        elif extension.lower() not in compiled_modules and not (ctx['PHP_VERSION'].startswith('7.2.') and extension.lower() == 'mcrypt'):
            print("The extension '%s' is not provided by this buildpack." % extension, file=os.sys.stderr)

    ctx['PHP_EXTENSIONS'] = filtered_extensions


def _parse_extensions_from_ini_file(file):
    extensions = []
    regex = re.compile(r'^extension\s*=\s*[\'\"]?(.*)\.so')

    with open(file, 'r') as f:
        for line in f:
            matches = regex.findall(line)
            if len(matches) == 1:
                extensions.append(matches[0])

    return extensions

def validate_php_ini_extensions(ctx):
    all_supported =  _get_supported_php_extensions(ctx) + _get_compiled_modules(ctx)
    ini_files = glob.glob(os.path.join(ctx["BUILD_DIR"], '.bp-config', 'php', 'php.ini.d', '*.ini'))

    for file in ini_files:
        extensions = _parse_extensions_from_ini_file(file)
        for ext in extensions:
            if ext not in all_supported:
                raise RuntimeError("The extension '%s' is not provided by this buildpack." % ext)


def include_fpm_d_confs(ctx):
    ctx['PHP_FPM_CONF_INCLUDE'] = ''
    php_fpm_d_path = os.path.join(ctx['BUILD_DIR'], '.bp-config', 'php', 'fpm.d')
    if len(glob.glob(os.path.join(php_fpm_d_path, '*.conf'))) > 0:
        ctx['PHP_FPM_CONF_INCLUDE'] = 'include=fpm.d/*.conf'


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

def warn_invalid_php_version(requested, default, docslink):
    warning = ("WARNING: PHP version {} not available, using default version ({}). "
               "In future versions of the buildpack, specifying a non-existent PHP version will cause staging to fail. "
               "See: {}")
    print(warning.format(requested, default, docslink))

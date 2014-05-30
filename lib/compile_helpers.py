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
from build_pack_utils import FileUtil


_log = logging.getLogger('helpers')


class FakeBuilder(object):
    def __init__(self, ctx):
        self._ctx = ctx


class FakeInstaller(object):
    def __init__(self, builder, installer):
        self._installer = installer
        self.builder = builder


def setup_htdocs_if_it_doesnt_exist(ctx):
    if is_web_app(ctx):
        htdocsPath = os.path.join(ctx['BUILD_DIR'], 'htdocs')
        if not os.path.exists(htdocsPath):
            fu = FileUtil(FakeBuilder(ctx), move=True)
            fu.under('BUILD_DIR')
            fu.into('htdocs')
            fu.where_name_does_not_match(
                '^%s.*$' % os.path.join(ctx['BUILD_DIR'], '.bp'))
            fu.where_name_does_not_match(
                '^%s.*$' % os.path.join(ctx['BUILD_DIR'], '.extensions'))
            fu.where_name_does_not_match(
                '^%s.*$' % os.path.join(ctx['BUILD_DIR'], '.bp-config'))
            fu.where_name_does_not_match(
                '^%s.*$' % os.path.join(ctx['BUILD_DIR'], 'manifest.yml'))
            fu.where_name_does_not_match(
                '^%s.*$' % os.path.join(ctx['BUILD_DIR'], 'lib'))
            fu.done()


def convert_php_extensions(ctx):
    _log.debug('Converting PHP extensions')
    SKIP = ('cli', 'pear', 'cgi')
    ctx['PHP_EXTENSIONS'] = \
        "\n".join(["extension=%s.so" % ex
                   for ex in ctx['PHP_EXTENSIONS'] if ex not in SKIP])
    path = (ctx['PHP_VERSION'].startswith('5.4')) and \
        '@HOME/php/lib/php/extensions/no-debug-non-zts-20100525' or ''
    ctx['ZEND_EXTENSIONS'] = \
        "\n".join(['zend_extension="%s"' % os.path.join(path, "%s.so" % ze)
                   for ze in ctx['ZEND_EXTENSIONS']])


def build_php_environment(ctx):
    _log.debug('Building PHP environment variables')
    ctx["PHP_ENV"] = \
        "\n".join(["env[%s] = $%s" % (k, k) for k in os.environ.keys()])


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
            print 'Build pack could not find a PHP file to execute!'
            _log.info('Build pack could not find a file to execute.  Either '
                      'set "APP_START_CMD" or include one of these files [%s]',
                      ", ".join(possible_files))
            app = 'app.php'
    return app

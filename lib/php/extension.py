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
from compile_helpers import convert_php_extensions
from compile_helpers import build_php_environment


def preprocess_commands(ctx):
    return (('$HOME/.bp/bin/rewrite', '"$HOME/php/etc"'),
            ('$HOME/.bp/bin/rewrite', '"$HOME/.env"'))


def service_commands(ctx):
    return {
        'php-fpm': (
            '$HOME/php/sbin/php-fpm',
            '-p "$HOME/php/etc"',
            '-y "$HOME/php/etc/php-fpm.conf"'),
        'php-fpm-logs': (
            'tail',
            '-F $HOME/../logs/php-fpm.log')
    }


def service_environment(ctx):
    return {
        'LD_LIBRARY_PATH': '@LD_LIBRARY_PATH:@HOME/php/lib'
    }


def compile(install):
    print 'Installing PHP'
    convert_php_extensions(install.builder._ctx)
    build_php_environment(install.builder._ctx)
    (install
        .package('PHP')
        .config()
            .from_application('.bp-config/php')
            .or_from_build_pack('defaults/config/php/{PHP_VERSION}')
            .to('php/etc')
            .rewrite()
            .done()
        .modules('PHP')
            .find_modules_with_regex('^extension=(.*).so$')
            .from_application('php/etc/php.ini')
            .find_modules_with_regex('^zend_extension=(.*).so$')
            .from_application('php/etc/php.ini')
            .find_modules_with_regex('^zend_extension=".*/(.*).so"$')
            .from_application('php/etc/php.ini')
            .include_module('fpm')
            .done())
    return 0

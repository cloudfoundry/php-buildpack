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
import json
from dingus import Dingus
from nose.tools import eq_
from build_pack_utils import utils


class TestSessions(object):

    def __init__(self):
        self.extension_module = utils.load_extension('extensions/sessions')

    def test_load_session_name_contains_redis(self):
        ctx = json.load(open('tests/data/sessions/vcap_services_redis.json'))
        sessions = self.extension_module.SessionStoreConfig(ctx)
        eq_(self.extension_module.RedisSetup, type(sessions._load_session()))

    def test_load_session_name_contains_memcached(self):
        ctx = json.load(
            open('tests/data/sessions/vcap_services_memcached.json'))
        sessions = self.extension_module.SessionStoreConfig(ctx)
        eq_(self.extension_module.MemcachedSetup,
            type(sessions._load_session()))

    def test_load_session_no_service(self):
        sessions = self.extension_module.SessionStoreConfig({})
        eq_(None, sessions._load_session())

    def test_alt_name_logic_redis(self):
        redis = self.extension_module.RedisSetup({}, {})
        eq_('redis-sessions', redis.session_store_key())
        redis = self.extension_module.RedisSetup({
            'REDIS_SESSION_STORE_SERVICE_NAME': 'my-redis-db'
        }, {})
        eq_('my-redis-db', redis.session_store_key())

    def test_alt_name_logic_memcached(self):
        memcached = self.extension_module.MemcachedSetup({}, {})
        eq_('memcached-sessions', memcached.session_store_key())
        memcached = self.extension_module.MemcachedSetup({
            'MEMCACHED_SESSION_STORE_SERVICE_NAME': 'my-memcached-db'
        }, {})
        eq_('my-memcached-db', memcached.session_store_key())

    def test_load_session_alt_name(self):
        ctx = json.load(
            open('tests/data/sessions/vcap_services_alt_name.json'))
        sessions = self.extension_module.SessionStoreConfig(ctx)
        eq_(None, sessions._load_session())
        ctx['REDIS_SESSION_STORE_SERVICE_NAME'] = 'php-session-db'
        eq_(self.extension_module.RedisSetup, type(sessions._load_session()))

    def test_should_compile(self):
        sessions = self.extension_module.SessionStoreConfig({})
        sessions._load_session = Dingus(return_value=object())
        eq_(True, sessions._should_compile())

    def test_load_session_redis_but_not_for_sessions(self):
        ctx = json.load(open('tests/data/sessions/'
                             'vcap_services_with_redis_not_for_sessions.json'))
        sessions = self.extension_module.SessionStoreConfig(ctx)
        eq_(None, sessions._load_session())

    def test_configure_adds_redis_extension(self):
        ctx = json.load(open('tests/data/sessions/vcap_services_redis.json'))
        ctx['PHP_EXTENSIONS'] = []
        sessions = self.extension_module.SessionStoreConfig(ctx)
        sessions._php_ini = Dingus()
        sessions.configure()
        eq_(True, 'redis' in ctx['PHP_EXTENSIONS'])

    def test_configure_adds_memcached_extension(self):
        ctx = json.load(
            open('tests/data/sessions/vcap_services_memcached.json'))
        ctx['PHP_EXTENSIONS'] = []
        sessions = self.extension_module.SessionStoreConfig(ctx)
        sessions._php_ini = Dingus()
        sessions.configure()
        eq_(True, 'memcached' in ctx['PHP_EXTENSIONS'])

    def test_configure_adds_redis_config_to_php_ini(self):
        ctx = json.load(open('tests/data/sessions/vcap_services_redis.json'))
        sessions = self.extension_module.SessionStoreConfig(ctx)
        sessions.load_config = Dingus()
        php_ini = Dingus()
        sessions._php_ini = php_ini
        sessions._php_ini_path = '/tmp/staged/app/php/etc/php.ini'
        sessions.compile(None)
        eq_(1, len(sessions.load_config.calls()))
        eq_(3, len(php_ini.update_lines.calls()))
        eq_(1, len(php_ini.save.calls()))
        eq_(4, len(php_ini.calls()))
        eq_('session.save_handler = redis',
            php_ini.update_lines.calls()[1].args[1])
        eq_('session.save_path = "tcp://redis-host:45629?auth=redis-pass"',
            php_ini.update_lines.calls()[2].args[1])

    def test_configure_adds_memcached_config_to_php_ini(self):
        ctx = json.load(
            open('tests/data/sessions/vcap_services_memcached.json'))
        sessions = self.extension_module.SessionStoreConfig(ctx)
        sessions.load_config = Dingus()
        php_ini = Dingus()
        sessions._php_ini = php_ini
        sessions._php_ini_path = '/tmp/staged/app/php/etc/php.ini'
        sessions.compile(None)
        eq_(1, len(sessions.load_config.calls()))
        eq_(3, len(php_ini.update_lines.calls()))
        eq_(1, len(php_ini.append_lines.calls()))
        eq_(True, all([arg.endswith('\n')
                       for arg in php_ini.append_lines.calls()[0].args[0]]),
            "Must end with EOL")
        eq_(1, len(php_ini.save.calls()))
        eq_(5, len(php_ini.calls()))
        eq_('session.save_handler = memcached',
            php_ini.update_lines.calls()[1].args[1])
        eq_('session.save_path = "PERSISTENT=app_sessions host:port"',
            php_ini.update_lines.calls()[2].args[1])

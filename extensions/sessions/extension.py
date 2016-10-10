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
"""Session Config Extension

Configures redis or memcached for session sharing
"""
from extension_helpers import PHPExtensionHelper


class BaseSetup(object):
    def __init__(self, ctx, info):
        self._ctx = ctx
        self._info = info
        self.creds = self._info.get('credentials', {})

    def session_store_key(self):
        key_name = self.DEFAULT_SESSION_STORE_TRIGGER
        if self.CUSTOM_SESSION_STORE_KEY_NAME in self._ctx:
            key_name = self._ctx[self.CUSTOM_SESSION_STORE_KEY_NAME]
        return key_name

    def custom_config_php_ini(self, php_ini):
        pass


class RedisSetup(BaseSetup):
    DEFAULT_SESSION_STORE_TRIGGER = 'redis-sessions'
    CUSTOM_SESSION_STORE_KEY_NAME = 'REDIS_SESSION_STORE_SERVICE_NAME'
    EXTENSION_NAME = 'redis'

    def __init__(self, ctx, info):
        BaseSetup.__init__(self, ctx, info)

    def session_save_path(self):
        return "tcp://%s:%s?auth=%s" % (
            self.creds.get('hostname',
                           self.creds.get('host', 'not-found')),
            self.creds.get('port', 'not-found'),
            self.creds.get('password', ''))

class MemcachedSetup(BaseSetup):
    DEFAULT_SESSION_STORE_TRIGGER = 'memcached-sessions'
    CUSTOM_SESSION_STORE_KEY_NAME = 'MEMCACHED_SESSION_STORE_SERVICE_NAME'
    EXTENSION_NAME = 'memcached'

    def __init__(self, ctx, info):
        BaseSetup.__init__(self, ctx, info)

    def session_save_path(self):
        return 'PERSISTENT=app_sessions %s' % self.creds.get('servers',
                                                             'not-found')

    def custom_config_php_ini(self, php_ini):
        php_ini.append_lines([
            'memcached.sess_binary=On\n',
            'memcached.use_sasl=On\n',
            'memcached.sess_sasl_username=%s\n' % self.creds.get('username',
                                                                 ''),
            'memcached.sess_sasl_password=%s\n' % self.creds.get('password', '')
        ])

class SessionStoreConfig(PHPExtensionHelper):
    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)
        self.service = None

    def _should_compile(self):
        if self.service is None:
            self.service = self._load_session()
        return self.service is not None

    def _load_session(self):
        # load search keys
        session_types = [
            RedisSetup,
            MemcachedSetup
        ]
        # search for an appropriately name session store
        vcap_services = self._ctx.get('VCAP_SERVICES', {})
        for provider, services in vcap_services.iteritems():
            for service in services:
                service_name = service.get('name', '')
                for session_type in session_types:
                    session = session_type(self._ctx, service)
                    if service_name.find(session.session_store_key()) != -1:
                        return session

    def _configure(self):
        # load the PHP extension that provides session save handler
        if self.service is not None:
            self._ctx.get('PHP_EXTENSIONS',
                          []).append(self.service.EXTENSION_NAME)

    def _compile(self, install):
        # modify php.ini to contain the right session config
        self.load_config()
        self._php_ini.update_lines(
            '^session\.name = JSESSIONID$',
            'session.name = PHPSESSIONID')
        self._php_ini.update_lines(
            '^session\.save_handler = files$',
            'session.save_handler = %s' % self.service.EXTENSION_NAME)
        self._php_ini.update_lines(
            '^session\.save_path = "@{TMPDIR}"$',
            'session.save_path = "%s"' % self.service.session_save_path())
        self.service.custom_config_php_ini(self._php_ini)
        self._php_ini.save(self._php_ini_path)


SessionStoreConfig.register(__name__)

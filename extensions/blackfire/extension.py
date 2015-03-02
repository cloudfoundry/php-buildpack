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
"""Blackfire Extension

Downloads, installs and configures the Blackfire agent for PHP
"""
import os
import os.path
import logging
from extension_helpers import PHPExtensionHelper


_log = logging.getLogger('blackfire')


class BlackfireExtension(PHPExtensionHelper):
    def __init__(self, ctx):
        self._log = _log
        self.server_id = None
        self.server_token = None
        PHPExtensionHelper.__init__(self, ctx)

    def _defaults(self):
        return {
            'BLACKFIRE_DOWNLOAD_HOST': 'packages.blackfire.io',
            'BLACKFIRE_AGENT_VERSION': '0.20.0',
            'BLACKFIRE_PROBE_VERSION': '0.20.5',
            'BLACKFIRE_AGENT_DOWNLOAD_URL': 'http://{BLACKFIRE_DOWNLOAD_HOST}/binaries/blackfire-agent/{BLACKFIRE_AGENT_VERSION}/blackfire-agent-linux_amd64.tar.gz',
            'BLACKFIRE_AGENT_HASH_DOWNLOAD_URL': 'http://{BLACKFIRE_DOWNLOAD_HOST}/binaries/blackfire-agent/{BLACKFIRE_AGENT_VERSION}/blackfire-agent-linux_amd64.sha1',
            'BLACKFIRE_AGENT_PACKAGE_INSTALL_DIR': 'blackfire/agent',
            'BLACKFIRE_AGENT_STRIP': False,
            'BLACKFIRE_PROBE_DOWNLOAD_URL': 'http://{BLACKFIRE_DOWNLOAD_HOST}/binaries/blackfire-php/{BLACKFIRE_PROBE_VERSION}/blackfire-php-linux_amd64-php-{BLACKFIRE_PROBE_PHP_VERSION}.tar.gz',
            'BLACKFIRE_PROBE_HASH_DOWNLOAD_URL': 'http://{BLACKFIRE_DOWNLOAD_HOST}/binaries/blackfire-php/{BLACKFIRE_PROBE_VERSION}/blackfire-php-linux_amd64-php-{BLACKFIRE_PROBE_PHP_VERSION}.sha',
            'BLACKFIRE_PROBE_PACKAGE_INSTALL_DIR': 'blackfire/probe',
            'BLACKFIRE_PROBE_STRIP': False
        }

    def _should_compile(self):
        services = self._services.get('blackfire', [])
        enabled = False
        if len(services) == 0:
            self._log.info("Blackfire services not detected.")
        if len(services) > 1:
            self._log.warn("Multiple Blackfire services found,"
                           " credentials from first one.")
        if len(services) > 0:
            credentials = services[0].get('credentials', {})
            self.server_id = credentials.get('serverId', None)
            self.server_token = credentials.get('serverToken', None)
            if self.server_id and self.server_token:
                self._log.debug("Blackfire service detected.")
                enabled = True

        if 'BLACKFIRE_SERVER_ID' in self._ctx.keys() and \
           'BLACKFIRE_SERVER_TOKEN' in self._ctx.keys():
            if enabled:
                self._log.warn("Detected a Blackfire Service and a Manual Key,"
                               " using the manual key.")
            self.server_id = self._ctx['BLACKFIRE_SERVER_ID']
            self.server_token = self._ctx['BLACKFIRE_SERVER_TOKEN']
            enabled = True

        if enabled:
            self.blackfire_so = os.path.join(self._ctx['BUILD_DIR'],
                                             'blackfire',
                                             'probe',
                                             'blackfire-%s.so' % self._get_api())
            self._log.debug("PHP Extension [%s]", self.blackfire_so)
            self.agent_path = os.path.join(self._ctx['BUILD_DIR'],
                                           'blackfire',
                                           'agent',
                                           'agent')
            self._log.debug("Agent [%s]", self.agent_path)
            self.agent_config_path = os.path.join(self._ctx['BUILD_DIR'],
                                                  'blackfire',
                                                  'agent',
                                                  'config.ini')
            self._log.debug("Agent configuration [%s]", self.agent_config_path)
            self.agent_socket_path = os.path.join(self._ctx['BUILD_DIR'],
                                                  'blackfire',
                                                  'agent',
                                                  'agent.sock')
            self._log.debug("Agent socket [%s]", self.agent_socket_path)

        return enabled

    def _service_commands(self):
        return {
            'blackfire-agent': (
                '$HOME/blackfire/agent/agent',
                '-config="$HOME/blackfire/agent/config.ini"',
                '-socket="unix://$HOME/blackfire/agent/agent.sock"')
        }

    def _compile(self, install):
        self._ctx['BLACKFIRE_PROBE_PHP_VERSION'] = self._ctx['PHP_VERSION'].replace('.', '')[0:2]
        install.package('BLACKFIRE_AGENT')
        install.package('BLACKFIRE_PROBE')
        self._update_php_ini()
        self._write_agent_configuration(self.agent_config_path)

    def _update_php_ini(self):
        self.load_config()
        self._php_ini.append_lines((
            'extension=%s\n' % self.blackfire_so,
            '\n'
            '[blackfire]\n',
            'blackfire.server_id=%s\n' % self.server_id,
            'blackfire.server_token=%s\n' % self.server_token,
            'blackfire.agent_socket=unix://%s\n' % self.agent_socket_path
        ))
        self._php_ini.save(self._php_ini_path)

    def _write_agent_configuration(self, config_path):
        directory = os.path.dirname(config_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(config_path, 'wt') as fd:
            fd.writelines((
                '[blackfire]\n',
                'server-id=e92fc80d-dc52-4cfb-8f4c-a8db940706f8\n',
                'server-token=101af42ab9afcd468a3d3e9f87565008b21262b6a3d7f50812d52c911ba3d698\n'
            ))
            fd.close()

# Register extension methods
BlackfireExtension.register(__name__)

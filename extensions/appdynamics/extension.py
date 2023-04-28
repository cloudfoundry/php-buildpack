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
"""AppDynamics Extension

Downloads, installs and configures the AppDynamics agent for PHP
"""
import os
import os.path
import logging
from extension_helpers import PHPExtensionHelper
from subprocess import call
import re

_log = logging.getLogger('appdynamics')

class AppDynamicsInstaller(PHPExtensionHelper):
    _detected = None                # Boolean to check if AppDynamics service is detected
    _FILTER = "app[-]?dynamics"
    _appdynamics_credentials = None # JSON which contains all appdynamics credentials
    _account_access_key = None      # AppDynamics Controller Account Access Key
    _account_name = None            # AppDynamics Controller Account Name
    _host_name = None               # AppDynamics Controller Host Address
    _port = None                    # AppDynamics Controller Port
    _ssl_enabled = None             # AppDynamics Controller SSL Enabled
    # Specify the Application details
    _app_name = None                # AppDynamics App name
    _tier_name = None               # AppDynamics Tier name
    _node_name = None               # AppDynamics Node name

    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)

    def _defaults(self):
        """Returns a set of default environment variables.

        Return a dictionary of default environment variables. These
        are merged with the build pack context when this the extension
        object is created.
        """
        return {
                'APPDYNAMICS_HOST': 'download.run.pivotal.io',
                'APPDYNAMICS_VERSION': '23.4.0-724',
                'APPDYNAMICS_PACKAGE': 'appdynamics-{APPDYNAMICS_VERSION}.tar.bz2',
                'APPDYNAMICS_DOWNLOAD_URL': 'https://{APPDYNAMICS_HOST}/appdynamics-php/{APPDYNAMICS_PACKAGE}'
        }

    def _should_compile(self):
        """
        Determines if the extension should install it's payload.

        This check is called during the `compile` method of the extension.
        It should return true if the payload of the extension should
        be installed (i.e. the `install` method is called).
        """
        if AppDynamicsInstaller._detected is None:
            VCAP_SERVICES_STRING = str(self._services)
            if bool(re.search(AppDynamicsInstaller._FILTER, VCAP_SERVICES_STRING)):
                print("AppDynamics service detected, beginning compilation")
                _log.info("AppDynamics service detected")
                AppDynamicsInstaller._detected = True
            else:
                AppDynamicsInstaller._detected = False
        return AppDynamicsInstaller._detected

    def _configure(self):
        """
        Configures the extension.

        Called when `should_configure` returns true.
        """
        print("Running AppDynamics extension method _configure")
        self._load_service_info()

    def _load_service_info(self):
        """
        Get Controller binding credentials and application details for AppDynamics service

        """
        print("Setting AppDynamics credentials info...")
        services = self._ctx.get('VCAP_SERVICES', {})
        service_defs = services.get("appdynamics")
        if service_defs is None:
            # Search in user-provided service
            print("No Marketplace AppDynamics services found")
            print("Searching for AppDynamics service in user-provided services")
            user_services = services.get("user-provided")
            for user_service in user_services:
                if bool(re.search(AppDynamicsInstaller._FILTER, user_service.get("name"))):
                    print("Using the first AppDynamics service present in user-provided services")
                    AppDynamicsInstaller._appdynamics_credentials = user_service.get("credentials")
                    self._load_service_credentials()
                    try:
                        # load the app details from user-provided service
                        print("Setting AppDynamics App, Tier and Node names from user-provided service")
                        AppDynamicsInstaller._app_name = AppDynamicsInstaller._appdynamics_credentials.get("application-name")
                        print("User-provided service application-name = " + AppDynamicsInstaller._app_name)
                        AppDynamicsInstaller._tier_name = AppDynamicsInstaller._appdynamics_credentials.get("tier-name")
                        print("User-provided service tier-name = " + AppDynamicsInstaller._tier_name)
                        AppDynamicsInstaller._node_name = AppDynamicsInstaller._appdynamics_credentials.get("node-name")
                        print("User-provided service node-name = " + AppDynamicsInstaller._node_name)
                    except Exception:
                        print("Exception occurred while setting AppDynamics App, Tier and Node names from user-provided service, using default naming")
                        self._load_app_details()
        elif len(service_defs) > 1:
            print("Multiple AppDynamics services found in VCAP_SERVICES, using credentials from first one.")
            AppDynamicsInstaller._appdynamics_credentials = service_defs[0].get("credentials")
            self._load_service_credentials()
            self._load_app_details()
        elif len(service_defs) == 1:
            print("AppDynamics service found in VCAP_SERVICES")
            AppDynamicsInstaller._appdynamics_credentials = service_defs[0].get("credentials")
            self._load_service_credentials()
            self._load_app_details()


    def _load_service_credentials(self):
        """
        Configure AppDynamics Controller Binding credentials
        Called when Appdynamics Service is detected

        """
        if (AppDynamicsInstaller._appdynamics_credentials is not None):
            print("Setting AppDynamics Controller Binding Credentials")
            try:
                AppDynamicsInstaller._host_name = AppDynamicsInstaller._appdynamics_credentials.get("host-name")
                AppDynamicsInstaller._port = AppDynamicsInstaller._appdynamics_credentials.get("port")
                AppDynamicsInstaller._account_name = AppDynamicsInstaller._appdynamics_credentials.get("account-name")
                AppDynamicsInstaller._account_access_key = AppDynamicsInstaller._appdynamics_credentials.get("account-access-key")
                AppDynamicsInstaller._ssl_enabled = AppDynamicsInstaller._appdynamics_credentials.get("ssl-enabled")
            except Exception:
                print("Error populating AppDynamics controller binding credentials")
        else:
            print("AppDynamics credentials empty")

    def _load_app_details(self):
        """
        Configure AppDynamics application details
        Called when AppDynamics Service is detected

        """
        print("Setting default AppDynamics App, Tier and Node names")
        try:
            AppDynamicsInstaller._app_name = self._application.get("space_name") + ":" + self._application.get("application_name")
            print("AppDymamics default application-name = " + AppDynamicsInstaller._app_name)
            AppDynamicsInstaller._tier_name = self._application.get("application_name")
            print("AppDynamics default tier-name = " + AppDynamicsInstaller._tier_name)
            AppDynamicsInstaller._node_name = AppDynamicsInstaller._tier_name
            print("AppDynamics default node-name = " + AppDynamicsInstaller._node_name)
        except Exception:
            print("Error populating default App, Tier and Node names")

    def _compile(self, install):
        """
        Install the payload of this extension.

        Called when `_should_compile` returns true.  This is responsible
        for installing the payload of the extension.

        The argument is the installer object that is passed into the
        `compile` method.
        """
        print("Downloading AppDynamics package...")
        install.package('APPDYNAMICS')
        print("Downloaded AppDynamics package")

    def _service_environment(self):
        """
        Sets environment variables for application container

        Returns dict of environment variables x[var]=val
        """
        print("Setting AppDynamics service environment variables")
        env = {
            'PHP_VERSION': "$(/home/vcap/app/php/bin/php-config --version | cut -d '.' -f 1,2)",
            'PHP_EXT_DIR': "$(/home/vcap/app/php/bin/php-config --extension-dir | sed 's|/tmp/staged|/home/vcap|')",
            'APPD_CONF_CONTROLLER_HOST': AppDynamicsInstaller._host_name,
            'APPD_CONF_CONTROLLER_PORT': AppDynamicsInstaller._port,
            'APPD_CONF_ACCOUNT_NAME': AppDynamicsInstaller._account_name,
            'APPD_CONF_ACCESS_KEY': AppDynamicsInstaller._account_access_key,
            'APPD_CONF_SSL_ENABLED': AppDynamicsInstaller._ssl_enabled,
            'APPD_CONF_APP': AppDynamicsInstaller._app_name,
            'APPD_CONF_TIER': AppDynamicsInstaller._tier_name,
            'APPD_CONF_NODE': AppDynamicsInstaller._node_name
        }
        return env

    # def _service_commands(self):

    def _preprocess_commands(self):
        """
        Commands that the build pack needs to run in the runtime container prior to the app starting.
        Use these sparingly as they run before the app starts and count against the time that an application has
        to start up successfully (i.e. if it takes too long app will fail to start).

        Returns list of commands
        """
        print("Running AppDynamics preprocess commands")
        commands = [
            [ 'echo "Installing AppDynamics package..."'],
            [ 'PHP_EXT_DIR=$(find /home/vcap/app -name "no-debug-non-zts*" -type d)'],
            [ 'chmod -R 755 /home/vcap'],
            [ 'chmod -R 777 /home/vcap/app/appdynamics/appdynamics-php-agent-linux_x64/logs'],
            [ 'if [ $APPD_CONF_SSL_ENABLED == \"true\" ] ; then export sslflag=-s ; '
              'echo sslflag set to $sslflag ; fi; '],
            [ '/home/vcap/app/appdynamics/appdynamics-php-agent-linux_x64/install.sh '
              '$sslflag '
              '-a "$APPD_CONF_ACCOUNT_NAME@$APPD_CONF_ACCESS_KEY" '
              '-e "$PHP_EXT_DIR" '
              '-p "/home/vcap/app/php/bin" '
              '-i "/home/vcap/app/appdynamics/phpini" '
              '-v "$PHP_VERSION" '
              '--ignore-permissions '
              '"$APPD_CONF_CONTROLLER_HOST" '
              '"$APPD_CONF_CONTROLLER_PORT" '
              '"$APPD_CONF_APP" '
              '"$APPD_CONF_TIER" '
              '"$APPD_CONF_NODE:$CF_INSTANCE_INDEX" '],
            [ 'cat /home/vcap/app/appdynamics/phpini/appdynamics_agent.ini >> /home/vcap/app/php/etc/php.ini'],
            [ 'echo "AppDynamics installation complete"']
        ]
        return commands

AppDynamicsInstaller.register(__name__)

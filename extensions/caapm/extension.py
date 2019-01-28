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
from subprocess import call

_log = logging.getLogger('CAAPM')


class CAAPMInstaller(object):
    def __init__(self, ctx):
        self._detected = None  # Boolean to check if caapm service is _detected
        self._servicefilter = "caapm"
        self._collport = None  # IA agent port
        self._collhost = None  # IA agent remote host/ip address
        self._appname = None  # PHP App name
	self._agenthostname = None  # PHP Probe agent hostname
	self._enabledBA = None  # browser agent support
	self._BACookieExpTime = None  # Browser agent cookie expiry time
        self._defaultappname = "PHP App"  # Default PHP App name
        self._defaultcollport = "5005"  # Default IA Agent Port
	self._defaultenabledBA = False  # By default browser agent support is disabled
        self._php_extn_dir = None            #parsed PHP extension directory
        self._php_ini_path = None            #parsed PHP INI Path
        self._logsDir = None
        self._log = _log
        self._ctx = ctx
        try:
            self._log.info("Initializing")
            if ctx['PHP_VM'] == 'php':
                self._merge_defaults()
                self._load_service_info()

        except Exception:
            self._log.exception("Error installing CA APM PHP Agent.")


    def _merge_defaults(self):
        for key, val in self._defaults().iteritems():
            if key not in self._ctx:
                self._ctx[key] = val

    def _defaults(self):
        self._log.info("Loading defaults info")

        return {
            'CA_APM_DOWNLOAD_HOST': 'ca.bintray.com/apm-agents',
            'CA_APM_DOWNLOAD_VERSION': '10.7.3',
            'CA_APM_PHP_PACKAGE': 'CA-APM-PHPAgent-{CA_APM_DOWNLOAD_VERSION}_linux.tar.gz',
            'CAAPM_DOWNLOAD_URL': 'https://{CA_APM_DOWNLOAD_HOST}/{CA_APM_PHP_PACKAGE}'
        }


    def _load_service_info(self):
        """
        Get IA agent details from caapm service
        """
        self._log.info("Loading service info to find CA APM Service")
        services = self._ctx.get('VCAP_SERVICES', {})
        service_defs = services.get(self._servicefilter)
        credentials = None
        if service_defs is None:
            # Search in user-provided service
            self._log.info("Searching for CA APM service in user-provided services")
            user_services = services.get("user-provided")
            for user_service in user_services:
                if self._servicefilter in user_service.get('name'):
                    print("Using the first CA APM service present in user-provided services")
                    self._log.info("Using the first CA APM service present in user-provided services")
                    serviceFound = True
                    credentials = user_service.get("credentials")
                    break
        elif len(service_defs) > 1:
            self._log.info("Multiple CA APM services found in VCAP_SERVICES, using properties from first one.")
            credentials = service_defs[0].get("credentials")
        elif len(service_defs) == 1:
            self._log.info("CA APM service found in VCAP_SERVICES")
            credentials = service_defs[0].get("credentials")

        if (credentials is not None):
            self._collport = credentials.get("collport")
            self._collhost = credentials.get("collhost")
            self._appname = credentials.get("appname")
	    self._agenthostname = credentials.get("agenthostname")
            self._enabledBA = credentials.get("enableBrowserAgentSupport")
	    self._BACookieExpTime = credentials.get("browserAgentCookieExpTime")
            self._detected = True
            self._log.debug("IA Agent Host [%s]", self._collhost)
            self._log.debug("IA Agent Port [%s]", self._collport)
            self._log.debug("PHP App Name [%s]", self._appname)
            if (self._collhost is None):
                 print("Error: CA APM service detected but required credential (collhost) is missing.Skipping the CA APM PHP Agent installation")
                 _log.error("CA APM service detected but required credential (collhost) is missing.Skipping the CA APM PHP Agent installation")
                 self._detected = False
        elif serviceFound:
            print("Error: CA APM service detected but required credential (collhost) is missing.Skipping the CA APM PHP Agent installation")
	    _log.error("CA APM service detected but required credential (collhost) is missing.Skipping the CA APM PHP Agent installation")
            self._detected = False


    def should_install(self):
        return self._detected


    def _set_php_extn_dir(self):
        self._php_ini_path = os.path.join(self._ctx['BUILD_DIR'], 'php', 'etc', 'php.ini')
        self._php_extn_dir = self._find_php_extn_dir().replace("@{HOME}", self._ctx['BUILD_DIR'])
        _log.debug("PHP Ext Directory [%s] and PHP INI path [%s]",self._php_extn_dir,self._php_ini_path)


    def _find_php_extn_dir(self):
        with open(self._php_ini_path, 'rt') as php_ini:
            for line in php_ini.readlines():
                if line.startswith('extension_dir'):
                    (key, val) = line.strip().split(' = ')
                    return val.strip('"')

    def _get_caapm_log_dir(self):
        if (self._logsDir is None):
            home = self._ctx['HOME'];
            caapm_home = os.path.join(home, 'app', 'caapm')
	    self._logsDir = os.path.join(caapm_home, 'apm-phpagent', 'probe', 'logs')
            if not os.path.exists(self._logsDir):
                os.makedirs(self._logsDir)
            _log.debug("Setting writable permissions to CA APM PHP Agent logs dir %s"  %self._logsDir)
            call([ 'chmod', '-R', '777', self._logsDir ])

    def _install_apm_agent(self):
        vcap_app = self._ctx.get('VCAP_APPLICATION', {})
        if (self._appname is None):
            self._appname = vcap_app.get('name', None)
            self._log.debug("App Name resolved is [%s]", self._appname)
            if (self._appname is None):
                self._appname = self._defaultappname;
        if (self._collport is None):
            self._collport = self._defaultcollport;
	if (self._agenthostname is None):
            vcap_app_uri = vcap_app.get('application_uris', None)
	    self._agenthostname = vcap_app_uri[0]
	if (self._enabledBA is None):
            self._enabledBA = self._defaultenabledBA;
	else :
	    lowerCaseValue = self._enabledBA.lower()
            if (lowerCaseValue in ['true','yes','1','enable']):
                self._enabledBA = True
            elif (lowerCaseValue in ['false','no','0','disable']):
                self._enabledBA = False
	    else:
	        self._enabledBA = self._defaultenabledBA

        print("Compiling CA APM PHP Agent install commands")
        _log.info("Compiling CA APM PHP Agent install commands")
	self._set_php_extn_dir()
        self._get_caapm_log_dir()
	builddir = self._ctx['BUILD_DIR'];
	phproot = os.path.join(builddir, 'php', 'bin')
	caapm_temp = os.path.join(builddir, 'caapm')
	caapm_ini = os.path.join(caapm_temp, 'wily_php_agent.ini')
        logsDirTemp = os.path.join(caapm_temp, 'apm-phpagent', 'probe', 'logs')

	installercmd = [caapm_temp +"/apm-phpagent/installer.sh"]
	installercmd.append('-appname')
        installercmd.append('"'+ self._appname + '"')
	installercmd.append('-iaport')
        installercmd.append('%s' %self._collport)
	installercmd.append('-iahost')
        installercmd.append('%s' %self._collhost)
	installercmd.append('-logdir')
        installercmd.append('%s' %self._logsDir)
	installercmd.append('-ext')
        installercmd.append('%s' %self._php_extn_dir)
	installercmd.append('-phproot')
        installercmd.append('%s' %phproot)
	installercmd.append('-ini')
        installercmd.append('%s' %caapm_temp)
	installercmd.append('-agenthostname')
        installercmd.append('%s' %self._agenthostname)

	if (self._enabledBA):
            installercmd.append('-enableBrowserAgentSupport')
	    if(self._BACookieExpTime is not None) and (self._BACookieExpTime != 3):
	        installercmd.append('-browserAgentCookieExpTime')
                installercmd.append('%s' %self._BACookieExpTime)
	installercmd.append('-enableCFSupport')

        _log.debug("Compiled CA APM PHP Agent install commands %s"  %installercmd)
        print("Installing CA APM PHP Agent")
        _log.info("Installing CA APM PHP Agent");
        call(installercmd)

        print("Updating PHP INI file with CA APM PHP Agent Properties")
        _log.info("Updating PHP INI file with CA APM PHP Agent Properties")
        with open(caapm_ini, 'r') as caapm_php_ini:
            lines = caapm_php_ini.readlines()

        with open(self._php_ini_path, 'a+') as php_ini:
            for line in lines:
                php_ini.write(line)




def preprocess_commands(ctx):
    return ()


def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    caapmphp = CAAPMInstaller(install.builder._ctx)
    if caapmphp.should_install():
        _log.info("Downloading CA APM PHP Agent package...")
        print("Downloading CA APM PHP Agent package...")
        install.package('CAAPM')
        _log.info("Downloaded CA APM PHP Agent package")
        print("Downloaded CA APM PHP Agent package")
        caapmphp._install_apm_agent()
        caapmphp._get_caapm_log_dir()
        _log.debug("CA APM PHP Agent installation completed")

    return 0

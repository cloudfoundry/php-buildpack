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
from extension_helpers import PHPExtensionHelper
import re

_log = logging.getLogger('CAAPM')

class CAAPMInstaller(PHPExtensionHelper):
    _detected = None                # Boolean to check if introscope service is _detected    
    _servicefilter = "caapm"      
    _collport = None                # Collector agent port
    _collhost = None                # Collector agent remote host/ip address
    _appname = None                 # PHP App name
    _defaultappname = "PHP App"     # Default PHP App name    
    _defaultcollport = "5005"       # Default Collector Agent Port
    
    _php_extn_dir = None            #parsed PHP extension directory
    _php_ini_path = None            #parsed PHP INI Path
    
    
   
    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)        

    
    def _defaults(self):
        """
        Return a dictionary of default environment variables.
        """
        return {
                'CA_APM_DOWNLOAD_HOST': 'ca.bintray.com/apm-agents',
                'CA_APM_DOWNLOAD_VERSION': '10.6.0',
                'CA_APM_PHP_PACKAGE': 'CA-APM-PHPAgent-{CA_APM_DOWNLOAD_VERSION}_linux.tar.gz',
                'CAAPM_DOWNLOAD_URL': 'https://{CA_APM_DOWNLOAD_HOST}/{CA_APM_PHP_PACKAGE}'
        }
   
    
    def _should_compile(self):
        """
        Determines if the extension should install it's payload.
        This check is called during the `compile` method of the extension.
        It should return true if the payload of the extension should
        be installed (i.e. the `install` method is called).
        """
	if CAAPMInstaller._detected is None:
            VCAP_SERVICES_STRING = str(self._services)
            if bool(re.search(CAAPMInstaller._servicefilter, VCAP_SERVICES_STRING)):
                print("CA APM service _detected")
                _log.info("CA APM service _detected")		
                CAAPMInstaller._detected = True
            else:
                CAAPMInstaller._detected = False
        return CAAPMInstaller._detected

    def _configure(self):
        """
        Configures the extension.
        Called when `should_configure` returns true.
        """
        _log.debug("method: _configure")
        self._load_service_info()


    def _load_service_info(self):
        """
        Get info from CAAPM service
        """        
        services = self._ctx.get('VCAP_SERVICES', {})
        service_defs = services.get(CAAPMInstaller._servicefilter)
	credentials = None
	serviceFound = False
        if service_defs is None:
            # Search in user-provided service
            print("Searching for CA APM service in user-provided services")
            _log.debug("Searching for CA APM service in user-provided services")	
            user_services = services.get("user-provided")
            for user_service in user_services:
                if CAAPMInstaller._servicefilter in user_service.get('name'):
		    serviceFound = True	
                    print("Using the first CA APM service present in user-provided services")
                    _log.debug("Using the first CA APM service present in user-provided services")
                    credentials = user_service.get("credentials")                                       
                    break
        elif len(service_defs) > 1:
            print("Multiple CA APM services found in VCAP_SERVICES, using properties from first one.")
            _log.info("Multiple CA APM services found in VCAP_SERVICES, using properties from first one.")
            credentials = service_defs[0].get("credentials")        
        elif len(service_defs) == 1:
            print("CA APM service found in VCAP_SERVICES") 
            _log.info("CA APM service found in VCAP_SERVICES")
            credentials = service_defs[0].get("credentials")
	else:
	    CAAPMInstaller._detected = False	
		
        if (credentials is not None):	           
            CAAPMInstaller._collport = credentials.get("collport") 
            CAAPMInstaller._collhost = credentials.get("collhost")
	    CAAPMInstaller._appname = credentials.get("appname")
            _log.debug("IA Agent Host [%s]", self._collhost)
	    _log.debug("IA Agent Port [%s]", self._collport)
            _log.debug("PHP App Name [%s]", self._appname)
        elif serviceFound:
	    _log.error("CA APM service (caapm*) detected but required properties are missing!")
            CAAPMInstaller._detected = False
    
    def _compile(self, install):      
        print("Downloading CA APM PHP Agent package...")
        _log.info("Downloading CA APM PHP Agent package...")
        install.package('CAAPM')
        print("Downloaded CA APM PHP Agent package")
        _log.info("Downloaded CA APM PHP Agent package")

   
    def _service_environment(self):
        """
        Sets environment variables for application container
        
        """
        _log.info("Setting CA APM service environment variables")	

        if (CAAPMInstaller._appname is None):
            CAAPMInstaller._appname = CAAPMInstaller._defaultappname;
        if (CAAPMInstaller._collport is None):
            CAAPMInstaller._collport = CAAPMInstaller._defaultcollport;
	
        env = {               
            'CA_APM_COLLECTOR_PORT': CAAPMInstaller._collport,          
            'CA_APM_COLLECTOR_HOST': CAAPMInstaller._collhost,            
	    'CA_APM_PHP_APP_NAME':  "\"" + CAAPMInstaller._appname + "\""            
        }
        return env

   
    def _service_commands(self):
       return {}


    def _set_php_extn_dir(self):
        CAAPMInstaller._php_ini_path = os.path.join(self._ctx['BUILD_DIR'], 'php', 'etc', 'php.ini')
        CAAPMInstaller._php_extn_dir = self._find_php_extn_dir().replace("@{HOME}", self._ctx['HOME'] + "/app")              
        _log.debug("PHP Ext Directory [%s] and PHP INI path [%s]",CAAPMInstaller._php_extn_dir,CAAPMInstaller._php_ini_path)
        

    def _find_php_extn_dir(self):
        with open(CAAPMInstaller._php_ini_path, 'rt') as php_ini:
            for line in php_ini.readlines():
                if line.startswith('extension_dir'):
                    (key, val) = line.strip().split(' = ')
                    return val.strip('"')               
             
    
    def _preprocess_commands(self):
        """
        Commands that the build pack needs to run in the runtime container prior to the app starting.
        Use these sparingly as they run before the app starts and count against the time that an application has
        to start up successfully (i.e. if it takes too long app will fail to start).
        Returns list of commands
        """ 
	self._set_php_extn_dir()
	home = self._ctx['HOME'];	
	phproot = os.path.join(home, 'app', 'php', 'bin')
	phpini = os.path.join(home, 'app', 'php', 'etc', 'php.ini')	
	caapm_temp = os.path.join(home, 'app', 'caapm')	
	caapm_ini = os.path.join(caapm_temp, 'wily_php_agent.ini')
	logsDir = os.path.join(caapm_temp, 'apm-phpagent', 'probe', 'logs')
	
	installercmd = []	
	installercmd.append(caapm_temp +"/apm-phpagent/installer.sh -appname")
	installercmd.append(' "' + CAAPMInstaller._appname + '"')
	installercmd.append(' -collport %s' %CAAPMInstaller._collport)	
	installercmd.append(' -collhost %s' %CAAPMInstaller._collhost)
	installercmd.append(' -logdir %s' %logsDir)
	installercmd.append(' -ext %s' %CAAPMInstaller._php_extn_dir)
	installercmd.append(' -phproot %s' %phproot)
	installercmd.append(' -ini %s' %caapm_temp)
	
	
	print("Running CA APM preprocess commands")
       
        commands = [
            [ 'echo "Installing CA APM PHP Probe package..."'],                   
            [ 'chmod -R 777 %s' %logsDir]                              
        ]
        commands.append([' '.join(installercmd)])
        commands.append([ 'cat %s >> %s' %(caapm_ini, phpini)] )        
	
        _log.debug("Running CA APM preprocess commands %s"  %commands)    
        return commands


CAAPMInstaller.register(__name__)

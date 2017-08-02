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
from subprocess import call
import re

_log = logging.getLogger('CAAPM')

class CAAPMInstaller(PHPExtensionHelper):
    _detected = None                # Boolean to check if introscope service is _detected
    _FILTER = "introscope"    
    _emurl = None                   # EM Connection URL
    _collport = None                # Collector agent port
    _collipaddr = None              # Collector agent remote ip address
    _appname = None                 # PHP App name
    _defaultappname = "PHP App"     # Default PHP App name
    _defaultcollip = "127.0.0.1"    # Default Collector Agent IP
    _defaultcollport = "5005"       # Default Collector Agent Port
   
    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)           

    #0
    def _defaults(self):
        """Returns a set of default environment variables.

        Return a dictionary of default environment variables.
        """
        return {
                'CA_APM_DOWNLOAD_HOST': 'ca.bintray.com/apm-agents',
                'CA_APM_DOWNLOAD_VERSION': '10.5.2',
                'CA_APM_PHP_PACKAGE': 'CA-APM-PHPAgent-{CA_APM_DOWNLOAD_VERSION}_linux.tar.gz',
                'CAAPM_DOWNLOAD_URL': 'https://{CA_APM_DOWNLOAD_HOST}/{CA_APM_PHP_PACKAGE}'
        }
   

    #1
    def _should_compile(self):
        """
        Determines if the extension should install it's payload.

        This check is called during the `compile` method of the extension.
        It should return true if the payload of the extension should
        be installed (i.e. the `install` method is called).
        """
	if (CAAPMInstaller._supportedVersion is None):
	    phpver = self._ctx['PHP_VERSION']	   		
	    if (phpver == self._ctx['PHP_56_LATEST']) or (phpver.startswith('5.6')):
	        CAAPMInstaller._supportedVersion = True
	    else:
		print("CA APM PHP Agent doesn't support PHP Version %s." % phpver)
		_log.info("CA APM PHP Agent doesn't support PHP Version %s.", phpver)
	        CAAPMInstaller._supportedVersion = False		 
	        return CAAPMInstaller._supportedVersion
	        
	
	if not CAAPMInstaller._supportedVersion:
	    return CAAPMInstaller._supportedVersion

        if CAAPMInstaller._detected is None:
            VCAP_SERVICES_STRING = str(self._services)
            if bool(re.search(CAAPMInstaller._FILTER, VCAP_SERVICES_STRING)):
                print("CA APM service detected")
                _log.info("CA APM service detected")
                CAAPMInstaller._detected = True
            else:
                CAAPMInstaller._detected = False
        return CAAPMInstaller._detected

    def _configure(self):
        """
        Configures the extension.

        Called when `should_configure` returns true.
        """
        print("method: _configure")
        self._load_service_info()


    def _load_service_info(self):
        """
        Get emurl and collector port etc from introscope service

        """        
        services = self._ctx.get('VCAP_SERVICES', {})
        service_defs = services.get("introscope")
	credentials = None
        if service_defs is None:
            # Search in user-provided service
            print("Searching for CA APM service in user-provided services")
            user_services = services.get("user-provided")
            for user_service in user_services:
                if bool(re.search(CAAPMInstaller._FILTER, user_service.get("name"))):
                    print("Using the first CA APM service present in user-provided services")  
                    credentials = user_service.get("credentials")                                       
                    break
        elif len(service_defs) > 1:
            print("Multiple CA APM services found in VCAP_SERVICES, using properties from first one.")
            credentials = service_defs[0].get("credentials")        
        elif len(service_defs) == 1:
            print("CA APM service found in VCAP_SERVICES")   
            credentials = service_defs[0].get("credentials")           
		
        if (credentials is not None):		
            CAAPMInstaller._emurl = credentials.get("emurl")
            CAAPMInstaller._collport = credentials.get("collport") 
            CAAPMInstaller._collipaddr = credentials.get("collipaddr")          


    # 2
    def _compile(self, install):
      
        print("Downloading CA APM PHP Agent package...")
        install.package('CAAPM')
        print("Downloaded CA APM PHP Agent package")


    #3
    def _service_environment(self):
        """
        Sets environment variables for application container
        
        """
        print("Setting CA APM service environment variables")

        if (CAAPMInstaller._collipaddr is None):
            CAAPMInstaller._collipaddr = CAAPMInstaller._defaultcollip;
        if (CAAPMInstaller._appname is None):
            CAAPMInstaller._appname = CAAPMInstaller._defaultappname;
        if (CAAPMInstaller._collport is None):
            CAAPMInstaller._collport = CAAPMInstaller._defaultcollport;
        env = {           
            'CA_APM_EM_CONNECTION_URL': CAAPMInstaller._emurl,
            'CA_APM_COLLECTOR_PORT': CAAPMInstaller._collport,          
            'CA_APM_COLLECTOR_IP_ADDR': CAAPMInstaller._collipaddr
        }
        return env


    #4 (Done)
    def _service_commands(self):
       return {}

    #5
    def _preprocess_commands(self):
        """
        Commands that the build pack needs to run in the runtime container prior to the app starting.
        Use these sparingly as they run before the app starts and count against the time that an application has
        to start up successfully (i.e. if it takes too long app will fail to start).

        Returns list of commands
        """ 
        print("Running CA APM preprocess commands")
        commands = [
            [ 'echo "Installing CA APM PHP Probe package..."'],
            [ 'PHP_EXT_DIR=$(find /home/vcap/app -name "no-debug-non-zts*" -type d)'],           
            [ 'chmod -R 755 /home/vcap'],
            [ 'chmod -R 777 /home/vcap/app/caapm/apm-phpagent/probe/logs'],          
            [ '/home/vcap/app/caapm/apm-phpagent/installer.sh '             
              '-emurl "$CA_APM_EM_CONNECTION_URL" '
	      '-collport "$CA_APM_COLLECTOR_PORT" '
              '-collipaddr "$CA_APM_COLLECTOR_IP_ADDR" '          
              '-logdir "/home/vcap/app/caapm/apm-phpagent/probe/logs" '
              '-ext "$PHP_EXT_DIR" '
              '-phproot "/home/vcap/app/php/bin" '
              '-ini "/home/vcap/app/caapm" '],           
            [ 'cat /home/vcap/app/caapm/wily_php_agent.ini >> /home/vcap/app/php/etc/php.ini']                    
        ]

        if (CAAPMInstaller._collipaddr is None) or (CAAPMInstaller._collipaddr == "127.0.0.1") or (CAAPMInstaller._collipaddr == "localhost") or (CAAPMInstaller._collipaddr == "::1") or (CAAPMInstaller._collipaddr == "0:0:0:0:0:0:0:1"):
            commands.append(['/home/vcap/app/caapm/apm-phpagent/collector/bin/CollectorAgent.sh start'])         
        commands.append(['echo CA APM PHP Probe installation complete'])
             
        return commands


CAAPMInstaller.register(__name__)

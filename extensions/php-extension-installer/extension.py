import os
import os.path
import shutil
import logging

_log = logging.getLogger('php-extension-installer')

#Helper class to find custom PHP extensions and their dependent libraries
#provided with an application.  Entrier are added to php.ini for extensions,
#and dependant libraries are copied to php/lib.
class PHPExtensionInstaller(object):

    #Create and set local variables
    def __init__(self, ctx):
        self._log = _log
        self._log.info("Initializing PHPExtensionsInstaller")
        self._ctx = ctx
        #if self._ctx['APP_PHP_EXTENSIONS_DIR']:
        if 'APP_PHP_EXTENSIONS_DIR' in self._ctx:
            self._extensions_dir_name = self._ctx['APP_PHP_EXTENSIONS_DIR']
        else:
            self._extensions_dir_name = ".php-extensions"
        self._new_php_extensions_dir = os.path.join(self._ctx['BUILD_DIR'], self._ctx['WEBDIR'], self._extensions_dir_name)
        self._new_php_extensions_libs_dir = os.path.join(self._new_php_extensions_dir, 'lib')
        self._new_php_extensions = []
        self._new_php_extensions_libs = []
        self._lib_dir = os.path.join(self._ctx['PHP_INSTALL_PATH'], self._ctx['LIBDIR'])

    #Identify any extensions directory in the app (default: .php-extensions), and any dependencies
    #in the lib sub-directory.
    def _identify_new_extensions_and_libs(self):
        self._log.info("Looking for any custom PHP extensions")
        for root, dirs, files in os.walk(self._new_php_extensions_dir):
            for f in files:
                if root == self._new_php_extensions_dir and '.so' in f:
                    #chop /tmp off the front so it matches the deployed path not the staging one
                    deployed_root = root[4:]
                    self._new_php_extensions.append(os.path.join(deployed_root,f))
                elif root == self._new_php_extensions_libs_dir and '.so' in f:
                    self._new_php_extensions_libs.append(os.path.join(root,f))
        if len(self._new_php_extensions) > 0:
            self._log.info("Found PHP extensions" + ", ".join(self._new_php_extensions))
        if len(self._new_php_extensions_libs) > 0:
            self._log.info("Found PHP extension dependencies" + ", ".join(self._new_php_extensions_libs))

    #For each found extension, write a line "extension=/path/to/extension.so" in php.ini
    def update_php_ini(self):
        if len(self._new_php_extensions) == 0:
            return
        self._log.info("Updating PHP ini")
        self.php_ini_path = os.path.join(self._ctx['BUILD_DIR'], 'php', 'etc', 'php.ini')
        with open(self.php_ini_path, 'rt') as php_ini:
            lines = php_ini.readlines()
        extns = [line for line in lines if line.startswith('extension=')]
        if len(extns) > 0:
            pos = lines.index(extns[-1]) + 1
        else:
            pos = lines.index('#{PHP_EXTENSIONS}\n') + 1
        for f in self._new_php_extensions:
            self._log.info("Adding %s to php.ini" % f)
            lines.insert(pos, 'extension=%s\n' % f)
        with open(self.php_ini_path, 'wt') as php_ini:
            for line in lines:
                php_ini.write(line)

    #Copy php extensions dependent libraries to the php/lib dir
    def copy_new_extensions_libs(self):
        if len(self._new_php_extensions_libs) == 0:
            return
        self._log.info("Copying dependent libraries to php/lib")
        for f in self._new_php_extensions_libs:
            self._log.info("copying %s to %s" % (f, self._lib_dir))
            shutil.copy(f, self._lib_dir)

#(Buildpack extension entry point)
#If running in a PHP context, create the helper class to look for and enable custom
#PHP extensions and their dependent libraries.
def compile(install):
    _log.info('Running the PHP Extension Installer buildpack extension')
    try:
        if install.builder._ctx['PHP_VM'] == 'php':
            phpExtnInstaller = PHPExtensionInstaller(install.builder._ctx)
            phpExtnInstaller._identify_new_extensions_and_libs()
            phpExtnInstaller.update_php_ini()
            phpExtnInstaller.copy_new_extensions_libs()
        else:
            _log("Trying to run extension outside of PHP context.  ctx[PHP_VM] should be php, but is "+ctx['PHP_VM'])
    except Exception, e:
        _log.exception("Error installing custom PHP Extensions:\n%s\n" % e.args)
        print("Error installing custom PHP Extensions:\n%s\n" % e.args)
        return 1
    return 0

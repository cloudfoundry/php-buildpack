import os
from build_pack_utils import utils


class PHPExtensionHelper(object):
    """A helper class for making extensions to the cf-php-build-pack"""

    def __init__(self, ctx):
        self._ctx = ctx
        self._services = self._ctx.get('VCAP_SERVICES', {})
        self._application = self._ctx.get('VCAP_APPLICATION', {})
        self._merge_defaults()
        self._php_ini = None
        self._php_fpm = None
        self._php_api = None

    def load_config(self):
        if not self._php_ini:
            self._php_ini_path = os.path.join(self._ctx['BUILD_DIR'], 'php',
                                              'etc', 'php.ini')
            self._php_ini = utils.ConfigFileEditor(self._php_ini_path)
        if not self._php_fpm:
            self._php_fpm_path = os.path.join(self._ctx['BUILD_DIR'], 'php',
                                              'etc', 'php-fpm.conf')
            self._php_fpm = utils.ConfigFileEditor(self._php_fpm_path)
        if not self._php_api:
            self._php_api = self._get_api()

    def _get_api(self):
        if self._ctx['PHP_VERSION'].startswith('5.4'):
            return '20100525'
        elif self._ctx['PHP_VERSION'].startswith('5.5'):
            return '20121212'
        elif self._ctx['PHP_VERSION'].startswith('5.6'):
            return '20131226'

    def _merge_defaults(self):
        for key, val in self._defaults().iteritems():
            if key not in self._ctx:
                self._ctx[key] = val

    def _defaults(self):
        """Returns a set of default environment variables.

        Create and return a list of default environment variables.  These
        are merged with the build pack context when this the extension
        object is created.

        Return a dictionary.
        """
        return {}

    def _should_compile(self):
        """Determines if the extension should install it's payload.

        This check is called during the `compile` method of the extension.
        It should return true if the payload of this extension should
        be installed (i.e. the `install` method is called).
        """
        return False

    def _should_configure(self):
        """Determines if the extension should configure itself.

        This check is called during the `configure` method of the
        extension.  It should return true if the extension should
        configure itself (i.e. the `configure` method is called).
        """
        return self._should_compile()

    def _compile(self, install):
        """Install the payload of this extension.

        Called when `_should_compile` returns true.  This is responsible
        for installing the payload of the extension.

        The argument is the installer object that is passed into the
        `compile` method.
        """
        pass

    def _configure(self):
        """Configure the extension.

        Called when `should_configure` returns true.  Implement this
        method for your extension.
        """
        pass

    def _preprocess_commands(self):
        """Return your list of preprocessing commands"""
        return ()

    def _service_commands(self):
        """Return dict of commands to run x[name]=cmd"""
        return {}

    def _service_environment(self):
        """Return dict of environment variables x[var]=val"""
        return {}

    def configure(self):
        """Configure extension.

        This method maps to the extension's `configure` method.
        """
        if self._should_configure():
            self._configure()

    def preprocess_commands(self):
        """Return list of preprocess commands to run once.

        This method maps to the extension's `preprocess_commands` method.
        """
        return (self._should_compile() and
                self._preprocess_commands() or ())

    def service_commands(self):
        """Return dictionary of service commands to run and keep running.

        This method maps to the extension's `service_commands` method.
        """
        return (self._should_compile() and
                self._service_commands() or {})

    def service_environment(self):
        """Return dictionary of environment for the service commands.

        This method maps to the extension's `service_environment` method.
        """
        return (self._should_compile() and
                self._service_environment() or {})

    def compile(self, install):
        """Build and install the extension.

        This method maps to the extension's `compile` method.
        """
        if self._should_compile():
            self._compile(install)
        return 0

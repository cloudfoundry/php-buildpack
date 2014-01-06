import os
from build_pack_utils import Installer
from build_pack_utils import CloudFoundryInstaller


class HttpdModuleInstaller(object):
    def __init__(self, builder):
        self._builder = builder
        self._installer = CloudFoundryInstaller(self._builder._ctx)
        self._modules = []

    def _load_modules(self, path):
        modules = []
        with open(path, 'rt') as f:
            for line in f:
                if line.startswith('LoadModule'):
                    (cmd, mod, modPath) = line.strip().split(' ')
                    modules.append(
                        modPath.split('/')[-1].strip('.so'))
        return modules

    def from_config(self, path):
        for base in (self._ctx['BP_DIR'], self._ctx['BUILD_DIR']):
            fullPath = os.path.join(base, path)
            if os.path.exists(fullPath):
                if os.path.isdir(fullPath):
                    for root, dirs, files in os.walk(fullPath):
                        for f in files:
                            if f.endswith('.conf'):
                                self._modules.extend(
                                    self._load_modules(
                                        os.path.join(root, f)))
                else:
                    assert os.path.isfile(fullPath), "should be a file"
                    self._modules.extend(
                        self._load_modules(fullPath))
            else:
                raise ValueError("path [%s] does not exist" % fullPath)

    def done(self):
        for module in self._modules:
            self._installer.install_binary_direct(
                os.path.join('{HTTPD_DOWNLOAD_PREFIX}',
                             "httpd-%s-{HTTPD_VERSION}.tar.gz"),
                os.path.join('{HTTPD_DOWNLOAD_PREFIX}',
                             "httpd-%s-{HTTPD_VERSION}.tar.gz.sha1"),
                os.path.join(self._builder._ctx['BUILD_DIR'],
                             'httpd', 'modules'))


def modules(self):
    return HttpdModuleInstaller(self.builder)


# add methods to Installer
Installer.modules = modules


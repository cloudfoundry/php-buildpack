import os
from build_pack_utils import Installer
from build_pack_utils import CloudFoundryInstaller


class HttpdModuleInstaller(object):
    def __init__(self, builder, installer):
        self._builder = builder
        self._installer = installer
        self._cf = CloudFoundryInstaller(self._builder._ctx)
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
        paths = (self._builder._ctx['BP_DIR'],
                 self._builder._ctx['BUILD_DIR'])
        for base in paths:
            fullPath = os.path.join(base, path)
            if os.path.exists(fullPath) and os.path.isdir(fullPath):
                for root, dirs, files in os.walk(fullPath):
                    for f in files:
                        if f.endswith('.conf'):
                            self._modules.extend(
                                self._load_modules(
                                    os.path.join(root, f)))
            elif os.path.exists(fullPath) and os.path.isfile(fullPath):
                self._modules.extend(
                    self._load_modules(fullPath))
        self._modules = list(set(self._modules))
        return self

    def done(self):
        if len(self._modules) == 0:
            print 'No modules detected :('
        for module in self._modules:
            self._builder._ctx['HTTPD_MODULE_NAME'] = module
            url = self._builder._ctx['HTTPD_MODULES_PATTERN']
            hashUrl = url + ".sha1"
            toPath = os.path.join(self._builder._ctx['BUILD_DIR'], 'httpd')
            self._cf.install_binary_direct(url, hashUrl, toPath, True)
        if 'HTTPD_MODULE_NAME' in self._builder._ctx.keys():
            del self._builder._ctx['HTTPD_MODULE_NAME']
        return self._installer


def modules(self):
    return HttpdModuleInstaller(self.builder, self)


# add methods to Installer
Installer.modules = modules


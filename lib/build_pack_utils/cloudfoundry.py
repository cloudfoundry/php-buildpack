import os
import sys
import json
import tempfile
import shutil
from zips import UnzipUtil
from hashes import HashUtil
from cache import DirectoryCacheManager
from downloads import Downloader
from downloads import CurlDownloader


class CloudFoundryUtil(object):
    @staticmethod
    def initialize():
        # Open stdout unbuffered
        if hasattr(sys.stdout, 'fileno'):
            sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
        ctx = {}
        # Build Pack Location
        ctx['BP_DIR'] = os.path.dirname(os.path.dirname(sys.argv[0]))
        # User's Application Files, build droplet here
        ctx['BUILD_DIR'] = sys.argv[1]
        # Cache space for the build pack
        ctx['CACHE_DIR'] = (len(sys.argv) == 3) and sys.argv[2] or None
        # Temp space
        ctx['TEMP_DIR'] = os.environ.get('TMPDIR', tempfile.gettempdir())
        tempfile.tempdir = ctx['TEMP_DIR']
        # Memory Limit
        ctx['MEMORY_LIMIT'] = os.environ.get('MEMORY_LIMIT', None)
        # Make sure cache & build directories exist
        if not os.path.exists(ctx['BUILD_DIR']):
            os.makedirs(ctx['BUILD_DIR'])
        if ctx['CACHE_DIR'] and not os.path.exists(ctx['CACHE_DIR']):
            os.makedirs(ctx['CACHE_DIR'])
        return ctx

    @staticmethod
    def load_json_config_file_from(folder, cfgFile):
        return CloudFoundryUtil.load_json_config_file(os.path.join(folder,
                                                                   cfgFile))

    @staticmethod
    def load_json_config_file(cfgPath):
        if os.path.exists(cfgPath):
            with open(cfgPath, 'rt') as cfgFile:
                return json.load(cfgFile)
        return {}


class CloudFoundryInstaller(object):
    def __init__(self, ctx):
        self._ctx = ctx
        self._unzipUtil = UnzipUtil(ctx)
        self._hashUtil = HashUtil(ctx)
        self._dcm = DirectoryCacheManager(ctx)
        self._dwn = self._get_downloader(ctx)(ctx)

    def _get_downloader(self, ctx):
        method = ctx.get('DOWNLOAD_METHOD', 'python')
        if method == 'python':
            return Downloader
        elif method == 'curl':
            return CurlDownloader
        elif method == 'custom':
            fullClsName = ctx['DOWNLOAD_CLASS']
            dotLoc = fullClsName.rfind('.')
            if dotLoc >= 0:
                clsName = fullClsName[dotLoc + 1: len(fullClsName)]
                modName = fullClsName[0:dotLoc]
                m = __import__(modName, globals(), locals(), [clsName])
                try:
                    return getattr(m, clsName)
                except AttributeError:
                    print 'WARNING: DOWNLOAD_CLASS not found!'
            else:
                print 'WARNING: DOWNLOAD_CLASS invalid, must include ' \
                      'package name!'
        return Downloader

    @staticmethod
    def _safe_makedirs(path):
        try:
            os.makedirs(path)
        except OSError, e:
            # Ignore if it exists
            if e.errno != 17:
                raise e

    def install_binary(self, installKey):
        fileName = self._ctx['%s_PACKAGE' % installKey]
        digest = self._ctx['%s_PACKAGE_HASH' % installKey]
        # check cache & compare digest
        # use cached file or download new
        # download based on ctx settings
        fileToInstall = self._dcm.get(fileName, digest)
        if fileToInstall is None:
            fileToInstall = os.path.join(self._ctx['TEMP_DIR'], fileName)
            self._dwn.download(
                os.path.join(self._ctx['%s_DOWNLOAD_PREFIX' % installKey],
                             fileName),
                fileToInstall)
            digest = self._hashUtil.calculate_hash(fileToInstall)
            fileToInstall = self._dcm.put(fileName, fileToInstall, digest)
        # unzip
        # install to ctx determined location 'PACKAGE_INSTALL_DIR'
        #  into or CF's BUILD_DIR
        pkgKey = '%s_PACKAGE_INSTALL_DIR' % installKey
        stripKey = '%s_STRIP' % installKey
        installIntoDir = os.path.join(
            self._ctx.get(pkgKey, self._ctx['BUILD_DIR']),
            installKey.lower())
        return self._unzipUtil.extract(fileToInstall,
                                       installIntoDir,
                                       self._ctx.get(stripKey, False))

    def install_from_build_pack(self, bpFile, toLocation=None):
        """Copy file from the build pack to the droplet

        Copies a file from the build pack to the application droplet.

            bpFile     -> file to copy, relative build pack
            toLocation -> optional location where to copy the file
                          relative to app droplet.  If not specified
                          uses the bpFile path.
        """
        fullPathFrom = os.path.join(self._ctx['BP_DIR'], bpFile)
        if os.path.exists(fullPathFrom) and os.path.isfile(fullPathFrom):
            fullPathTo = os.path.join(
                self._ctx['BUILD_DIR'],
                ((toLocation is None) and bpFile or toLocation))
            self._safe_makedirs(os.path.dirname(fullPathTo))
            shutil.copy(fullPathFrom, fullPathTo)

    def install_from_application(self, cfgFile, toLocation):
        """Copy file from one place to another in the application

        Copies a file from one place to another place within the
        application droplet.

            cfgFile    -> file to copy, relative build pack
            toLocation -> location where to copy the file,
                          relative to app droplet.
        """
        fullPathFrom = os.path.join(self._ctx['BUILD_DIR'], cfgFile)
        if os.path.exists(fullPathFrom) and os.path.isfile(fullPathFrom):
            fullPathTo = os.path.join(self._ctx['BUILD_DIR'], toLocation)
            self._safe_makedirs(os.path.dirname(fullPathTo))
            shutil.copy(fullPathFrom, fullPathTo)

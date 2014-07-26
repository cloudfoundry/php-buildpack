import os
import sys
import json
import tempfile
import shutil
import utils
import logging
from urlparse import urlparse
from zips import UnzipUtil
from hashes import HashUtil
from cache import DirectoryCacheManager
from downloads import Downloader
from downloads import CurlDownloader
from utils import safe_makedirs
from utils import find_git_url


_log = logging.getLogger('cloudfoundry')


class CloudFoundryUtil(object):
    @staticmethod
    def initialize():
        # Open stdout unbuffered
        if hasattr(sys.stdout, 'fileno'):
            sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
        ctx = utils.FormattedDict()
        # Add environment variables
        ctx.update(os.environ)
        # Convert JSON env variables
        ctx['VCAP_APPLICATION'] = json.loads(ctx.get('VCAP_APPLICATION',
                                                     '{}',
                                                     format=False))
        ctx['VCAP_SERVICES'] = json.loads(ctx.get('VCAP_SERVICES',
                                                  '{}',
                                                  format=False))
        # Build Pack Location
        ctx['BP_DIR'] = os.path.dirname(os.path.dirname(sys.argv[0]))
        # User's Application Files, build droplet here
        ctx['BUILD_DIR'] = sys.argv[1]
        # Cache space for the build pack
        ctx['CACHE_DIR'] = (len(sys.argv) == 3) and sys.argv[2] or None
        # Temp space
        if 'TMPDIR' not in ctx.keys():
            ctx['TMPDIR'] = tempfile.gettempdir()
        # Make sure cache & build directories exist
        if not os.path.exists(ctx['BUILD_DIR']):
            os.makedirs(ctx['BUILD_DIR'])
        if ctx['CACHE_DIR'] and not os.path.exists(ctx['CACHE_DIR']):
            os.makedirs(ctx['CACHE_DIR'])
        # Add place holder for extensions
        ctx['EXTENSIONS'] = []
        # Init Logging
        CloudFoundryUtil.init_logging(ctx)
        _log.info('CloudFoundry Initialized.')
        _log.debug("CloudFoundry Context Setup [%s]", ctx)
        # Git URL, if one exists
        ctx['BP_GIT_URL'] = find_git_url(ctx['BP_DIR'])
        _log.info('Build Pack Version: %s', ctx['BP_GIT_URL'])
        return ctx

    @staticmethod
    def init_logging(ctx):
        logFmt = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
        if ctx.get('BP_DEBUG', False):
            logging.basicConfig(level=logging.DEBUG, format=logFmt)
        else:
            logLevelStr = ctx.get('BP_LOG_LEVEL', 'INFO')
            logLevel = getattr(logging, logLevelStr, logging.INFO)
            logDir = os.path.join(ctx['BUILD_DIR'], '.bp', 'logs')
            safe_makedirs(logDir)
            logging.basicConfig(level=logLevel, format=logFmt,
                                filename=os.path.join(logDir, 'bp.log'))

    @staticmethod
    def load_json_config_file_from(folder, cfgFile):
        return CloudFoundryUtil.load_json_config_file(os.path.join(folder,
                                                                   cfgFile))

    @staticmethod
    def load_json_config_file(cfgPath):
        if os.path.exists(cfgPath):
            _log.debug("Loading config from [%s]", cfgPath)
            with open(cfgPath, 'rt') as cfgFile:
                return json.load(cfgFile)
        return {}


class CloudFoundryInstaller(object):
    def __init__(self, ctx):
        self._log = _log
        self._ctx = ctx
        self._unzipUtil = UnzipUtil(ctx)
        self._hashUtil = HashUtil(ctx)
        self._dcm = DirectoryCacheManager(ctx)
        self._dwn = self._get_downloader(ctx)(ctx)

    def _get_downloader(self, ctx):
        method = ctx.get('DOWNLOAD_METHOD', 'python')
        if method == 'python':
            self._log.debug('Using python downloader.')
            return Downloader
        elif method == 'curl':
            self._log.debug('Using cURL downloader.')
            return CurlDownloader
        elif method == 'custom':
            fullClsName = ctx['DOWNLOAD_CLASS']
            self._log.debug('Using custom downloader [%s].', fullClsName)
            dotLoc = fullClsName.rfind('.')
            if dotLoc >= 0:
                clsName = fullClsName[dotLoc + 1: len(fullClsName)]
                modName = fullClsName[0:dotLoc]
                m = __import__(modName, globals(), locals(), [clsName])
                try:
                    return getattr(m, clsName)
                except AttributeError:
                    self._log.exception(
                        'WARNING: DOWNLOAD_CLASS not found!')
            else:
                self._log.error(
                    'WARNING: DOWNLOAD_CLASS invalid, must include '
                    'package name!')
        return Downloader

    def _is_url(self, val):
        return urlparse(val).scheme != ''

    def install_binary_direct(self, url, hsh, installDir,
                              fileName=None, strip=False,
                              extract=True):
        self._log.debug("Installing direct [%s]", url)
        if not fileName:
            fileName = url.split('/')[-1]
        if self._is_url(hsh):
            digest = self._dwn.download_direct(hsh)
        else:
            digest = hsh
        self._log.debug(
            "Installing [%s] with digest [%s] into [%s] with "
            "name [%s] stripping [%s]",
            url, digest, installDir, fileName, strip)
        fileToInstall = self._dcm.get(fileName, digest)
        if fileToInstall is None:
            self._log.debug('File [%s] not in cache.', fileName)
            fileToInstall = os.path.join(self._ctx['TMPDIR'], fileName)
            self._dwn.download(url, fileToInstall)
            digest = self._hashUtil.calculate_hash(fileToInstall)
            fileToInstall = self._dcm.put(fileName, fileToInstall, digest)
        if extract:
            return self._unzipUtil.extract(fileToInstall,
                                           installDir,
                                           strip)
        else:
            shutil.copy(fileToInstall, installDir)
            return installDir

    def install_binary(self, installKey):
        self._log.debug('Installing [%s]', installKey)
        url = self._ctx['%s_DOWNLOAD_URL' % installKey]
        hashUrl = self._ctx.get(
            '%s_HASH_DOWNLOAD_URL' % installKey,
            "%s.%s" % (url, self._ctx['CACHE_HASH_ALGORITHM']))
        installDir = os.path.join(self._ctx['BUILD_DIR'],
                                  self._ctx.get(
                                      '%s_PACKAGE_INSTALL_DIR' % installKey,
                                      installKey.lower()))
        strip = self._ctx.get('%s_STRIP' % installKey, False)
        return self.install_binary_direct(url, hashUrl, installDir,
                                          strip=strip)

    def _install_from(self, fromPath, fromLoc, toLocation=None, ignore=None):
        """Copy file or directory from a location to the droplet

        Copies a file or directory from a location to the application
        droplet. Directories are copied recursively, but specific files
        in those directories can be ignored by specifing the ignore parameter.

            fromPath   -> file to copy, relative build pack
            fromLoc    -> root of the from path.  Full path to file or
                          directory to be copied is fromLoc + fromPath
            toLocation -> optional location where to copy the file
                          relative to app droplet.  If not specified
                          uses fromPath.
            ignore     -> an optional callable that is passed to
                          the ignore argument of shutil.copytree.
        """
        self._log.debug("Install file [%s] from [%s]", fromPath, fromLoc)
        fullPathFrom = os.path.join(fromLoc, fromPath)
        if os.path.exists(fullPathFrom):
            fullPathTo = os.path.join(
                self._ctx['BUILD_DIR'],
                ((toLocation is None) and fromPath or toLocation))
            safe_makedirs(os.path.dirname(fullPathTo))
            self._log.debug("Copying [%s] to [%s]", fullPathFrom, fullPathTo)
            if os.path.isfile(fullPathFrom):
                shutil.copy(fullPathFrom, fullPathTo)
            else:
                utils.copytree(fullPathFrom, fullPathTo, ignore=ignore)

    def install_from_build_pack(self, fromPath, toLocation=None, ignore=None):
        """Copy file or directory from the build pack to the droplet

        Copies a file or directory from the build pack to the application
        droplet. Directories are copied recursively, but specific files
        in those directories can be ignored by specifing the ignore parameter.

            fromPath   -> file to copy, relative build pack
            toLocation -> optional location where to copy the file
                          relative to app droplet.  If not specified
                          uses fromPath.
            ignore     -> an optional callable that is passed to
                          the ignore argument of shutil.copytree.
        """
        self._install_from(
            fromPath,
            self._ctx['BP_DIR'],
            toLocation,
            ignore)

    def install_from_application(self, fromPath, toLocation, ignore=None):
        """Copy file or directory from one place to another in the application

        Copies a file or directory from one place to another place within the
        application droplet.

            fromPath   -> file or directory to copy, relative
                          to application droplet.
            toLocation -> location where to copy the file,
                          relative to app droplet.
            ignore     -> optional callable that is passed to the
                          ignore argument of shutil.copytree
        """
        self._install_from(
            fromPath,
            self._ctx['BUILD_DIR'],
            toLocation,
            ignore)

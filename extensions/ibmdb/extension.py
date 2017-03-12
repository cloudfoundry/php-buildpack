import json
import logging
import os
import re
import StringIO
import subprocess
import sys
from urlparse import urlparse
from build_pack_utils import stream_output
from build_pack_utils import utils
from extension_helpers import ExtensionHelper

#from build_pack_utils.downloads import Downloader
#from build_pack_utils.zips import UnzipUtil

#_log = logging.getLogger(os.path.basename(os.path.dirname(__file__)))

# Lets say there are two extensions e1 and e2 each with following methods used by buildpack
#   configure; compile; service_environment; service_commands; preprocess_commands
# The order in which these are called is as follows:
#  1) e1.configure
#  2) e2.configure
#  3) Rewrite httpd.conf
#  4) Extract and install httpd
#  5) Rewrite php.ini
#  6) Extract and install php
#  7) e1.compile
#  8) e2.compile
#  9) e1.service_environment
# 10) e2.service_environment
# 11) e1.service_commands
# 10) e2.service_commands
# 13) e1.preprocess_commands
# 14) e2.preprocess_commands

CONSTANTS = {
    'PHP_ARCH': '64',           # if not 64, 32-bit is assumed
    'PHP_THREAD_SAFETY': 'nts', # if not ts, nts is assumed, case-insensitive
}

PKGDOWNLOADS = {
    # 10/Mar/2017: IBM DB CLI Driver now downloaded directly from IBM site. A suggestion was given to IBM dev team
    # that maintains this archive to have the version number as part of the archive name. The DLURL will need to be
    # modified when they do.
    'IBMDBCLIDRIVER_VERSION': '11.1',
    'IBMDBCLIDRIVER_REPOSITORY': 'https://public.dhe.ibm.com/ibmdl/export/pub/software/data/db2/drivers/odbc_cli',
    'IBMDBCLIDRIVER_DLFILE': 'linuxx64_odbc_cli.tar.gz',
    'IBMDBCLIDRIVER_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/{IBMDBCLIDRIVER_DLFILE}',

    'IBM_DB2_VERSION': '1.9.9',
    'IBM_DB2_REPOSITORY': 'https://github.com/fishfin/ibmdb-extensions-linuxx64',
    'IBM_DB2_DLFILE': 'ibm_db2-v{IBM_DB2_VERSION}.tar.gz',
    'IBM_DB2_DLURL': '{IBM_DB2_REPOSITORY}/raw/master/{IBM_DB2_DLFILE}',

    # 10/Mar/2017: Added PDO support
    'PDO_IBM_VERSION': '1.3.4',
    'PDO_IBM_REPOSITORY': 'https://github.com/fishfin/ibmdb-extensions-linuxx64',
    'PDO_IBM_DLFILE': 'pdo_ibm-v{PDO_IBM_VERSION}.tar.gz',
    'PDO_IBM_DLURL': '{PDO_IBM_REPOSITORY}/raw/master/{PDO_IBM_DLFILE}',
}

class IBMDBInstaller(ExtensionHelper):

    def __init__(self, ctx):
        self._log = logging.getLogger(os.path.basename(os.path.dirname(__file__)))

        ExtensionHelper.__init__(self, ctx)
        self._log.info('Detected PHP Version ' + self._ctx['PHP_VERSION'])
        self._log.info('Using build pack directory ' + self._ctx['BP_DIR'])
        self._log.info('Using build directory ' + self._ctx['BUILD_DIR'])

        self._ibmdbClidriverBaseDir = 'ibmdb_clidriver'
        self._phpRoot = os.path.join(self._ctx['BUILD_DIR'], 'php')
        self._phpIniPath = os.path.join(self._phpRoot, 'etc', 'php.ini')
        self._phpExtnDir = os.path.join(self._phpRoot, 'lib', 'php', 'extensions')

        self._ctx['IBMDBCLIDRIVER_INSTALL_DIR'] = os.path.join(self._ctx['BUILD_DIR'], self._ibmdbClidriverBaseDir)

    def _defaults(self):
        pkgdownloads = PKGDOWNLOADS
        pkgdownloads['DOWNLOAD_DIR'] = os.path.join(self._ctx['BUILD_DIR'], '.downloads')        
        return utils.FormattedDict(pkgdownloads)

    def _should_configure(self):
        return False

    def _should_compile(self):
        return True

    def _configure(self):
        self._log.info(__file__ + "->configure")
        pass

    def _compile(self, install):
        self._log.info(__file__ + "->compile")
        self._installer = install._installer

        extnBaseDir = self._findPhpExtnBaseDir()
        self._zendModuleApiNo = extnBaseDir[len(extnBaseDir)-8:]
        self._phpExtnDir = os.path.join(self._phpExtnDir, extnBaseDir)
        #self._phpApi, self._phpZts = self._parsePhpApi()
        self.install_clidriver()
        self.install_extensions()
        self.cleanup()
        return 0

    def _service_environment(self):
        self._log.info(__file__ + "->service_environment")
        env = {
            #'IBM_DB_HOME': '$IBM_DB_HOME:$HOME/' + self._ibmdbClidriverBaseDir + '/lib',
            'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:$HOME/' + self._ibmdbClidriverBaseDir + '/lib',
            #'DB2_CLI_DRIVER_INSTALL_PATH': '$HOME/' + self._ibmdbClidriverBaseDir,
            'PATH': '$HOME/' + self._ibmdbClidriverBaseDir + '/bin:$HOME/'
                    + self._ibmdbClidriverBaseDir + '/adm:$PATH',
        }
        #self._log.info(env['IBM_DB_HOME'])
        return env

    def _service_commands(self):
        self._log.info(__file__ + "->service_commands")        
        return {}

    def _preprocess_commands(self):
        self._log.info(__file__ + "->preprocess_commands")
        return ()

    def _logMsg(self, logMsg):
        self._log.info(logMsg)
        print logMsg        

    def _install_direct(self, url, hsh, installDir, fileName=None, strip=False, extract=True):
        # hsh for future use
        if not fileName:
            fileName = urlparse(url).path.split('/')[-1]
        fileToInstall = os.path.join(self._ctx['TMPDIR'], fileName)
        self._runCmd(os.environ, self._ctx['BUILD_DIR'], ['rm', '-rf', fileToInstall])

        self._log.debug("Installing direct [%s]", url)
        self._installer._dwn.custom_extension_download(url, url, fileToInstall)

        if extract:
            return self._installer._unzipUtil.extract(fileToInstall, installDir, strip)
        else:
            shutil.copy(fileToInstall, installDir)
            return installDir

    def _runCmd(self, environ, currWorkDir, cmd, displayRunLog=False):
        stringioWriter = StringIO.StringIO()
        try:
            stream_output(stringioWriter,            #sys.stdout,
                          ' '.join(cmd),
                          env=environ,
                          cwd=currWorkDir,
                          shell=True)
            cmdOutput = stringioWriter.getvalue()
            if displayRunLog:
                self._logMsg(cmdOutput)
        except:
            cmdOutput = stringioWriter.getvalue()
            print '-----> Command failed'
            print cmdOutput
            raise
        return cmdOutput

    def _findPhpExtnBaseDir(self):
        with open(self._phpIniPath, 'rt') as phpIni:
            for line in phpIni.readlines():
                if line.startswith('extension_dir'):
                    (key, extnDir) = line.strip().split(' = ')
                    extnBaseDir = os.path.basename(extnDir.strip('"'))
                    return extnBaseDir

    def _parsePhpApi(self):
        tmp = os.path.basename(self._phpExtnDir)
        phpApi = tmp.split('-')[-1]
        phpZts = (tmp.find('non-zts') == -1)
        return phpApi, phpZts

    def _modifyPhpIni(self):
        self._log.info('Modifying ' + self._phpIniPath)
        with open(self._phpIniPath, 'rt') as phpIni:
            lines = phpIni.readlines()
        extns = [line for line in lines if line.startswith('extension=')]
        if len(extns) > 0:
            pos = lines.index(extns[-1]) + 1
        else:
            pos = lines.index('#{PHP_EXTENSIONS}\n') + 1
        lines.insert(pos, 'extension=ibm_db2.so\n')
        lines.insert(pos, 'extension=pdo.so\n')  # pdo_ibm.so requires pdo.so, so automatically activating it
                                                 # (pdo.so must be in php extensions directory, by default it is)
        lines.insert(pos, 'extension=pdo_ibm.so\n')
        #lines.append('\n')
        self._log.info('Writing ' + self._phpIniPath)
        with open(self._phpIniPath, 'wt') as phpIni:
            for line in lines:
                phpIni.write(line)

    def install_clidriver(self):
        for clidriverpart in ['IBMDBCLIDRIVER']:
            self._install_direct(
                self._ctx[clidriverpart + '_DLURL'],
                None,
                self._ctx['IBMDBCLIDRIVER_INSTALL_DIR'],
                self._ctx[clidriverpart + '_DLFILE'],
                True)

        self._logMsg ('Installed IBMDB CLI Drivers to ' + self._ctx['IBMDBCLIDRIVER_INSTALL_DIR'])

    def install_extensions(self):
        for ibmdbExtn in ['IBM_DB2', 'PDO_IBM']:
            extnDownloadDir = os.path.join(self._ctx['DOWNLOAD_DIR'],
                                       ibmdbExtn.lower() + '_extn-' + self._ctx[ibmdbExtn + '_VERSION'])
            self._install_direct(
                self._ctx[ibmdbExtn + '_DLURL'],
                None,
                extnDownloadDir,
                self._ctx[ibmdbExtn + '_DLFILE'],
                True)

            self._runCmd(os.environ, self._ctx['BUILD_DIR'],
                        ['mv',
                         os.path.join(extnDownloadDir, self._zendModuleApiNo, ibmdbExtn.lower() + '.so'),
                         self._phpExtnDir])

            self._logMsg ('Installed ' + ibmdbExtn + ' Extension to ' + self._phpExtnDir)

        self._modifyPhpIni()
        #self._log.info(os.getenv('PATH'))

    def cleanup(self):
        self._runCmd(os.environ, self._ctx['BUILD_DIR'], ['rm', '-rf', self._ctx['DOWNLOAD_DIR']])

IBMDBInstaller.register(__name__)

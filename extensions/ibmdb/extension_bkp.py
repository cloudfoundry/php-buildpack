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
    'IBMDBCLIDRIVER_INSTALLDIR' : 'ibmdb_clidriver',
    'PHP_ARCH': '64',           # if not 64, 32-bit is assumed
    'PHP_THREAD_SAFETY': 'nts', # if not ts, nts is assumed, case-insensitive
    'PHPIZE': {
        '5': 'phpize5',
        '7.0': 'phpize7.0',
    },
}

PKGDOWNLOADS =  {
    'PHPSOURCE_VERSION': '{PHP_VERSION}',
    'PHPSOURCE_DLFILE': 'php-{PHPSOURCE_VERSION}.tar.gz',
    'PHPSOURCE_DLURL': 'http://in1.php.net/distributions/{PHPSOURCE_DLFILE}',

    'IBMDBCLIDRIVER_VERSION': '11.1',
    'IBMDBCLIDRIVER_REPOSITORY': 'https://github.com/fishfin/ibmdb-drivers-linuxx64',
    'IBMDBCLIDRIVER1_DLFILE': 'ibm_data_server_driver_for_odbc_cli_linuxx64_v{IBMDBCLIDRIVER_VERSION}_1of2.tar.gz',
    'IBMDBCLIDRIVER1_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/raw/master/{IBMDBCLIDRIVER1_DLFILE}',
    'IBMDBCLIDRIVER2_DLFILE': 'ibm_data_server_driver_for_odbc_cli_linuxx64_v{IBMDBCLIDRIVER_VERSION}_2of2.tar.gz',
    'IBMDBCLIDRIVER2_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/raw/master/{IBMDBCLIDRIVER2_DLFILE}',
    #'IBMDBCLIDRIVER_VERSION': '10.x',
    #'IBMDBCLIDRIVER_DLFILE': 'linuxx64_odbc_cli.tar.gz',
    #'IBMDBCLIDRIVER_DLURL': 'https://public.dhe.ibm.com/ibmdl/export/pub/software/data/db2/drivers/odbc_cli/{IBMDBCLIDRIVER_DLFILE}',

    #'IBMDB_PHP64_DLFILE': 'db2_db2driver_for_php64_linuxx64_v11.1.tar.gz',
    #'IBMDB_PHP64_DLURL': '{IBMDB_DRIVERS_REPOSITORY}/raw/master/{IBMDB_PHP64_DLFILE}',
    #'IBMDB_PHP32_DLFILE': 'db2_db2driver_for_php32_linuxx64_v11.1.tar.gz',
    #'IBMDB_PHP32_DLURL': '{IBMDB_DRIVERS_REPOSITORY}/raw/master/{IBMDB_PHP32_DLFILE}',

    'M4_VERSION': '1.4.17',
    'M4_DLFILE': 'm4-{M4_VERSION}.tar.gz',
    'M4_DLURL': 'http://ftp.gnu.org/pub/gnu/m4/{M4_DLFILE}',

    'AUTOCONF_VERSION': '2.69',
    'AUTOCONF_DLFILE': 'autoconf-{AUTOCONF_VERSION}.tar.gz',
    'AUTOCONF_DLURL': 'http://ftp.gnu.org/gnu/autoconf/{AUTOCONF_DLFILE}',

    'IBM_DB2_VERSION': '1.9.9',
    'IBM_DB2_DLFILE': 'ibm_db2-{IBM_DB2_VERSION}.tgz',
    'IBM_DB2_DLURL': 'https://pecl.php.net/get/{IBM_DB2_DLFILE}',
}

class IBMDBInstaller(ExtensionHelper):

    def __init__(self, ctx):
        self._log = logging.getLogger(os.path.basename(os.path.dirname(__file__)))

        ExtensionHelper.__init__(self, ctx)
        self._log.info('Detected PHP Version ' + self._ctx['PHP_VERSION'])
        self._log.info('Using build pack directory ' + self._ctx['BP_DIR'])
        self._log.info('Using build directory ' + self._ctx['BUILD_DIR'])

        self._phpRoot = os.path.join(self._ctx['BUILD_DIR'], 'php')
        self._phpInstallDir = os.path.join(self._phpRoot, 'lib', 'php')
        self._phpBinDir = os.path.join(self._phpRoot, 'bin')
        self._phpBinPath = os.path.join(self._phpBinDir, 'php')
        self._phpIniDir = os.path.join(self._phpRoot, 'etc')
        self._phpIniPath = os.path.join(self._phpIniDir, 'php.ini')
        self._phpExtnDir = os.path.join(self._phpInstallDir, 'extensions')
        self._compilationEnv = os.environ
        self._phpizeDir = os.path.dirname(__file__)

    def _defaults(self):
        pkgdownloads = PKGDOWNLOADS
        pkgdownloads['COMPILATION_DIR'] = os.path.join(self._ctx['BUILD_DIR'], '.build_ibmdb_extension')
        pkgdownloads['DOWNLOAD_DIR'] = os.path.join('{COMPILATION_DIR}', '.downloads')        
        pkgdownloads['IBMDBCLIDRIVER_INSTALL_DIR'] = os.path.join(self._ctx['BUILD_DIR'], 'ibmdb_clidriver')
        pkgdownloads['PHPSOURCE_INSTALL_DIR'] = os.path.join('{COMPILATION_DIR}', 'php-{PHPSOURCE_VERSION}')
        pkgdownloads['M4_DLDIR'] = os.path.join('{DOWNLOAD_DIR}', 'm4-{M4_VERSION}')
        pkgdownloads['M4_INSTALL_DIR'] = os.path.join('{COMPILATION_DIR}', 'm4-{M4_VERSION}')
        pkgdownloads['AUTOCONF_DLDIR'] = os.path.join('{DOWNLOAD_DIR}', 'autoconf-{AUTOCONF_VERSION}')
        pkgdownloads['AUTOCONF_INSTALL_DIR'] = os.path.join('{COMPILATION_DIR}', 'autoconf-{AUTOCONF_VERSION}')
        pkgdownloads['IBM_DB2_DLDIR'] = os.path.join('{PHPSOURCE_INSTALL_DIR}', 'ext', 'ibm_db2')
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

        self._phpExtnDir = os.path.join(self._phpExtnDir, self._findPhpExtnBaseDir())
        self._phpApi, self._phpZts = self._parsePhpApi()
        #self.install_phpDevTools(install)
        self.install_phpsource()
        self.install_clidriver()
        self.install_buildtools()
        self.install_extensions()
        self.cleanup()
        return 0

    def _service_environment(self):
        self._log.info(__file__ + "->service_environment")
        env = {
            'IBM_DB_HOME': '$IBM_DB_HOME:$HOME/' + CONSTANTS['IBMDBCLIDRIVER_INSTALLDIR'] + '/lib',
            'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:$HOME/' + CONSTANTS['IBMDBCLIDRIVER_INSTALLDIR'] + '/lib',
            'DB2_CLI_DRIVER_INSTALL_PATH': '$HOME/' + CONSTANTS['IBMDBCLIDRIVER_INSTALLDIR'],
            'PATH': '$HOME/' + CONSTANTS['IBMDBCLIDRIVER_INSTALLDIR'] + '/bin:$HOME/'
                    + CONSTANTS['IBMDBCLIDRIVER_INSTALLDIR'] + '/adm:$PATH',
        }
        self._log.info(env['IBM_DB_HOME'])
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
            if displayRunLog:
                self._log.info(stringioWriter.getvalue())
        except:
            print '-----> Command failed'
            print stringioWriter.getvalue()
            raise

    def _findPhpizeFile(self, inDir, forPhpVersion):
        phpizeFilesInDir = [f for f in os.listdir(inDir)
                      if os.path.isfile(os.path.join(inDir, f)) and re.match(r'phpize.*', f)]
        #verSubver = forPhpVersion.split('.')
        #verPatterns = list()
        #for index, subver in verSubver:
        #    pass
        phpizeFile = 'phpize5'
        return phpizeFile

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
        lines.insert(pos, 'extension=pdo_ibm.so\n')
        #lines.append('\n')
        self._log.info('Writing ' + self._phpIniPath)
        with open(self._phpIniPath, 'wt') as phpIni:
            for line in lines:
                phpIni.write(line)

    def _buildPeclEnv(self):
        env = {}
        for key in os.environ.keys():
            val = self._ctx.get(key, '')
            env[key] = val if type(val) == str else json.dumps(val)

        env['LD_LIBRARY_PATH'] = os.path.join(self._ctx['BUILD_DIR'], 'php', 'lib')
        env['PATH'] = ':'.join(filter(None, [env.get('PATH', ''), self._phpBinDir]))
        env['IBM_DB_HOME'] = os.path.join(self._ctx['BUILD_DIR'], CONSTANTS['IBMDBCLIDRIVER_INSTALLDIR'])
        env['PHPRC'] = self._phpIniDir
        env['PHP_PEAR_PHP_BIN'] = self._phpBinPath
        env['PHP_PEAR_INSTALL_DIR'] = self._phpInstallDir
        return env

    def install_phpDevTools(self):
        self._runCmd(os.environ,
                     self._ctx['BUILD_DIR'],
                     ['apt-get', 'install', 'php5-dev'], False)

    def install_clidriver(self):
        for clidriverpart in ['ibmdbclidriver1', 'ibmdbclidriver2']:
            self._install_direct(
                self._ctx[clidriverpart.upper() + '_DLURL'],
                None,
                self._ctx['IBMDBCLIDRIVER_INSTALL_DIR'],
                self._ctx[clidriverpart.upper() + '_DLFILE'],
                True)

        self._compilationEnv['IBM_DB_HOME'] = self._ctx['IBMDBCLIDRIVER_INSTALL_DIR']
        self._logMsg ('Installed IBMDB CLI Drivers to ' + self._ctx['IBMDBCLIDRIVER_INSTALL_DIR'])

    def install_buildtools(self):
        for buildtool in ['m4', 'autoconf']:
            buildtoolDownloadDir = self._ctx[buildtool.upper() + '_DLDIR']
            buildtoolInstallDir = self._ctx[buildtool.upper() + '_INSTALL_DIR']
            self._install_direct(
                self._ctx[buildtool.upper() + '_DLURL'],
                None,
                buildtoolDownloadDir,
                self._ctx[buildtool.upper() + '_DLFILE'],
                True)

            self._runCmd(self._compilationEnv, buildtoolDownloadDir, ['./configure', '--prefix=' + buildtoolInstallDir])
            self._runCmd(self._compilationEnv, buildtoolDownloadDir, ['make'])
            self._runCmd(self._compilationEnv, buildtoolDownloadDir, ['make', 'install'])
            self._compilationEnv['PATH'] = os.path.join(buildtoolInstallDir, 'bin') + ':' + self._compilationEnv['PATH']
            self._logMsg('Installed ' + buildtool)

        self._compilationEnv['PHP_AUTOCONF'] = os.path.join(self._ctx['AUTOCONF_INSTALL_DIR'],
                                                            'autoconf', 'bin', 'autoconf')
        self._compilationEnv['PHP_AUTOHEADER'] = os.path.join(self._ctx['AUTOCONF_INSTALL_DIR'],
                                                            'autoconf', 'bin', 'autoheader')

    def install_phpsource(self):
        self._install_direct(
                self._ctx['PHPSOURCE_DLURL'],
                None,
                self._ctx['PHPSOURCE_INSTALL_DIR'],
                self._ctx['PHPSOURCE_DLFILE'],
                True)

        self._logMsg ('Installed PHP ' + self._ctx['PHPSOURCE_VERSION'] + ' source files')

    def install_extensions(self):
        for ibmdbExtn in ['ibm_db2']: #, 'PDO', 'PDO_IBM']:
            self._install_direct(
                self._ctx[ibmdbExtn.upper() + '_DLURL'],
                None,
                self._ctx[ibmdbExtn.upper() + '_DLDIR'],
                self._ctx[ibmdbExtn.upper() + '_DLFILE'],
                True)
            #self._runCmd(self._buildPeclEnv(),
            #             self._ctx['BUILD_DIR'],
            #             ['pecl', 'install', ibmdbExtn],
            #             True)
        self._compilationEnv['PATH'] = self._phpizeDir + ':' + self._phpBinDir + ':' + self._compilationEnv['PATH']
        self._compilationEnv['LD_LIBRARY_PATH'] = os.path.join(self._phpRoot, 'lib')
        self._compilationEnv['IBM_DB_HOME'] = self._ctx['IBMDBCLIDRIVER_INSTALL_DIR']
        self._compilationEnv['PHPRC'] = self._phpIniDir
        self._compilationEnv['PHPSOURCE_INSTALL_DIR'] = self._ctx['PHPSOURCE_INSTALL_DIR']
        self._compilationEnv['PHP_PEAR_PHP_BIN'] = self._phpBinPath
        self._compilationEnv['PHP_PEAR_INSTALL_DIR'] = self._phpInstallDir

        self._logMsg('Path is now: ' + self._compilationEnv['PATH'])
        phpizeSh = self._findPhpizeFile(self._phpizeDir, self._ctx['PHP_VERSION'])
        self._runCmd(self._compilationEnv, self._phpizeDir, ['chmod', '777', phpizeSh])
        self._runCmd(self._compilationEnv, self._ctx['IBM_DB2_DLDIR'], [phpizeSh])
        #self._runCmd(self._compilationEnv, self._ctx['IBM_DB2_DLDIR'], ['./configure', '--with-IBM_DB2=/path/to/DB2'])
        #self._runCmd(self._compilationEnv, self._ctx['IBM_DB2_DLDIR'], ['make'])
        #self._runCmd(self._compilationEnv, self._ctx['IBM_DB2_DLDIR'], ['make', 'install'])
        self._modifyPhpIni()
        #self._log.info(os.getenv('PATH'))

    def cleanup(self):
        self._runCmd(os.environ, self._ctx['BUILD_DIR'], ['rm', '-rf', self._ctx['DOWNLOAD_DIR']])

    def install_extensions_direct_dysfunctional(self, install):
        CONSTANTS['PHP_THREAD_SAFETY'] = CONSTANTS['PHP_THREAD_SAFETY'].lower()
        phpArch = '64' if CONSTANTS['PHP_ARCH'] == '64' else '32'
        tempDir = os.path.join(self._ctx['TMPDIR'], 'fishfin_deleteme')
        install._install_direct(
            self._ctx['IBMDB_PHP' + str(phpArch)  + '_DLURL'],
            None,
            tempDir,
            self._ctx['IBMDB_PHP' + str(phpArch)  + '_DLFILE'],
            True)

        #rmExtns = '*_nts.so' if CONSTANTS['PHP_THREAD_SAFETY'] == 'ts' else '*_ts.so'
        #self._runCmd(os.environ, tempDir, ['rm', '-f', rmExtns])
        self._runCmd(os.environ, tempDir,
            ['mv', 'ibm_db2*' + CONSTANTS['PHP_THREAD_SAFETY'] + '.so', os.path.join(self._phpExtnDir, 'ibm_db2.so')])
        self._runCmd(os.environ, tempDir,
            ['mv', 'pdo_ibm*' + CONSTANTS['PHP_THREAD_SAFETY'] + '.so', os.path.join(self._phpExtnDir, 'pdo_ibm.so')])
        self._runCmd(os.environ, tempDir, ['rm', '-rf', tempDir])

        self._modifyPhpIni()

        self._log.info(__file__ + "->install_extensions completed")

IBMDBInstaller.register(__name__)

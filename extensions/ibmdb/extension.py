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

PKGDOWNLOADS =  {
    'M4_VERSION': '1.4.18',
    'M4_DLFILE': 'm4-{M4_VERSION}.tar.gz',
    'M4_DLURL': 'http://ftp.gnu.org/pub/gnu/m4/{M4_DLFILE}',

    'AUTOCONF_VERSION': '2.69',
    'AUTOCONF_DLFILE': 'autoconf-{AUTOCONF_VERSION}.tar.gz',
    'AUTOCONF_DLURL': 'http://ftp.gnu.org/gnu/autoconf/{AUTOCONF_DLFILE}',

    'IBMDBCLIDRIVER_VERSION': '11.1',
    #'IBMDBCLIDRIVER_REPOSITORY': 'https://public.dhe.ibm.com/ibmdl/export/pub/software/data/db2/drivers/odbc_cli',
    #'IBMDBCLIDRIVER1_DLFILE': 'linuxx64_odbc_cli.tar.gz',
    #'IBMDBCLIDRIVER1_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/{IBMDBCLIDRIVER_DLFILE}',
    #'IBMDBCLIDRIVER2_DLFILE': '',    # intentionally kept blank
    #'IBMDBCLIDRIVER2_DLURL': '',     # intentionally kept blank

    'IBMDBCLIDRIVER_REPOSITORY': 'https://github.com/fishfin/ibmdb-extensions-linuxx64',
    'IBMDBCLIDRIVER1_DLFILE': 'ibm_data_server_driver_for_odbc_cli_linuxx64_v{IBMDBCLIDRIVER_VERSION}_1of2.tar.gz',
    'IBMDBCLIDRIVER1_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/raw/master/{IBMDBCLIDRIVER1_DLFILE}',
    'IBMDBCLIDRIVER2_DLFILE': 'ibm_data_server_driver_for_odbc_cli_linuxx64_v{IBMDBCLIDRIVER_VERSION}_2of2.tar.gz',
    'IBMDBCLIDRIVER2_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/raw/master/{IBMDBCLIDRIVER2_DLFILE}',

    'PHPSOURCE_VERSION': '{PHP_VERSION}',
    'PHPSOURCE_DLFILE': 'php-{PHPSOURCE_VERSION}.tar.gz',
    'PHPSOURCE_DLURL': 'http://in1.php.net/distributions/{PHPSOURCE_DLFILE}',

    'IBM_DB2_VERSION': '1.9.9',
    'IBM_DB2_DLFILE': 'ibm_db2-{IBM_DB2_VERSION}.tgz',
    'IBM_DB2_DLURL': 'https://pecl.php.net/get/{IBM_DB2_DLFILE}',

    'PDO_IBM_VERSION': '1.3.4',
    'PDO_IBM_DLFILE': 'PDO_IBM-{PDO_IBM_VERSION}.tgz',
    'PDO_IBM_DLURL': 'https://pecl.php.net/get/{PDO_IBM_DLFILE}',
}

class IBMDBInstaller(ExtensionHelper):

    def __init__(self, ctx):
        self._log = logging.getLogger(os.path.basename(os.path.dirname(__file__)))

        ExtensionHelper.__init__(self, ctx)
        self._compilationEnv = os.environ
        if 'IBM_DB_HOME' not in self._compilationEnv:
            self._compilationEnv['IBM_DB_HOME'] = ''
        if 'LD_LIBRARY_PATH' not in self._compilationEnv:
            self._compilationEnv['LD_LIBRARY_PATH'] = ''
        if 'PATH' not in self._compilationEnv:
            self._compilationEnv['PATH'] = ''
        if 'PHPRC' not in self._compilationEnv:
            self._compilationEnv['PHPRC'] = ''
        if 'PHP_PEAR_INSTALL_DIR' not in self._compilationEnv:
            self._compilationEnv['PHP_PEAR_INSTALL_DIR'] = ''
        if 'PHP_PEAR_PHP_BIN' not in self._compilationEnv:
            self._compilationEnv['PHP_PEAR_PHP_BIN'] = ''

        self._log.info('Detected PHP Version ' + self._ctx['PHP_VERSION'])
        self._log.info('Using build pack directory ' + self._ctx['BP_DIR'])
        self._log.info('Using build directory ' + self._ctx['BUILD_DIR'])

        self._ibmdbClidriverBaseDir = 'ibmdb_clidriver'
        self._phpBuildRootDpath = os.path.join(self._ctx['BUILD_DIR'], 'php')
        self._phpBuildBinDpath = os.path.join(self._phpBuildRootDpath, 'bin')
        self._phpBuildBinFpath = os.path.join(self._phpBuildRootDpath, 'bin', 'php')
        self._phpBuildConfigFpath = os.path.join(self._phpBuildRootDpath, 'bin', 'php-config')
        self._phpBuildIniFpath = os.path.join(self._phpBuildRootDpath, 'etc', 'php.ini')
        self._phpizeShBuildFpath = os.path.join(self._phpBuildBinDpath, 'phpize')
        self._cfPHPConfigPrefixDir = ''
        self._cfPHPConfigExtnDir = ''
        self._phpExtnDir = ''
        self._zendModuleApiNo = ''
        self._phpExtnDpath = ''

    def _defaults(self):
        pkgdownloads = PKGDOWNLOADS
        pkgdownloads['COMPILATION_DIR'] = os.path.join(self._ctx['BUILD_DIR'], '.build_ibmdb_extension')
        pkgdownloads['DOWNLOAD_DIR'] = os.path.join('{COMPILATION_DIR}', '.downloads')        
        pkgdownloads['M4_DLDIR'] = os.path.join('{DOWNLOAD_DIR}', 'm4-{M4_VERSION}')
        pkgdownloads['M4_INSTALL_DIR'] = os.path.join('{COMPILATION_DIR}', 'm4-{M4_VERSION}')
        pkgdownloads['AUTOCONF_DLDIR'] = os.path.join('{DOWNLOAD_DIR}', 'autoconf-{AUTOCONF_VERSION}')
        pkgdownloads['AUTOCONF_INSTALL_DIR'] = os.path.join('{COMPILATION_DIR}', 'autoconf-{AUTOCONF_VERSION}')
        pkgdownloads['IBMDBCLIDRIVER_INSTALL_DIR'] = os.path.join(self._ctx['BUILD_DIR'], 'ibmdb_clidriver')
        pkgdownloads['PHPSOURCE_INSTALL_DIR'] = os.path.join('{COMPILATION_DIR}', 'php')
        pkgdownloads['IBM_DB2_DLDIR'] = os.path.join('{PHPSOURCE_INSTALL_DIR}', 'ext', 'ibm_db2')
        pkgdownloads['IBM_DB2_WITH_OPTS'] = ''
        pkgdownloads['PDO_IBM_DLDIR'] = os.path.join('{PHPSOURCE_INSTALL_DIR}', 'ext', 'pdo_ibm')
        pkgdownloads['PDO_IBM_WITH_OPTS'] = '--with-pdo-ibm={IBMDBCLIDRIVER_INSTALL_DIR}'
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

        self._cfPHPConfigPrefixDir = self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'],
                                        [self._phpBuildConfigFpath, '--prefix']).strip()
        self._cfPHPConfigExtnDir = self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'],
                                        [self._phpBuildConfigFpath, '--extension-dir']).strip()
        self._phpExtnDir = self.findPhpExtnBaseDir()
        self._zendModuleApiNo = self._phpExtnDir[len(self._phpExtnDir)-8:]
        self._phpExtnDpath = os.path.join(self._phpBuildRootDpath, 'lib', 'php', 'extensions', self._phpExtnDir)

        #self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'], ['shopt', '-s', 'dotglob'])

        #self._phpApi, self._phpZts = self._parsePhpApi()
        self.install_buildtools()
        self.install_clidriver()
        self.install_phpsource()
        self.download_extensions()
        self.modifyPhpIni()
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

    def findPhpExtnBaseDir(self):
        with open(self._phpBuildIniFpath, 'rt') as phpIni:
            for line in phpIni.readlines():
                if line.startswith('extension_dir'):
                    (key, extnDir) = line.strip().split(' = ')
                    extnBaseDir = os.path.basename(extnDir.strip('"'))
                    return extnBaseDir

    def modifyPhpIni(self):
        self._log.info('Modifying ' + self._phpBuildIniFpath)
        with open(self._phpBuildIniFpath, 'rt') as phpIni:
            lines = phpIni.readlines()
        extns = [line for line in lines if line.startswith('extension=')]
        if len(extns) > 0:
            pos = lines.index(extns[-1]) + 1
        else:
            pos = lines.index('#{PHP_EXTENSIONS}\n') + 1
        lines.insert(pos, 'extension=ibm_db2.so\n')
        lines.insert(pos, 'extension=pdo.so\n')
        lines.insert(pos, 'extension=pdo_ibm.so\n')
        #lines.append('\n')
        self._log.info('Writing ' + self._phpBuildIniFpath)
        with open(self._phpBuildIniFpath, 'wt') as phpIni:
            for line in lines:
                phpIni.write(line)

    def install_buildtools(self):
        self._logMsg('-- Installing Build Tools ------------------------')
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

        self._compilationEnv['PHP_AUTOCONF'] = os.path.join(self._ctx['AUTOCONF_INSTALL_DIR'], 'bin', 'autoconf')
        self._compilationEnv['PHP_AUTOHEADER'] = os.path.join(self._ctx['AUTOCONF_INSTALL_DIR'], 'bin', 'autoheader')
        self._logMsg('-- Installed Build Tools -------------------------')

    def install_clidriver(self):
        self._logMsg('-- Installing IBM DB CLI Drivers -----------------')
        for clidriverpart in ['ibmdbclidriver1', 'ibmdbclidriver2']:
            if self._ctx[clidriverpart.upper() + '_DLFILE'] != '':
                self._install_direct(
                    self._ctx[clidriverpart.upper() + '_DLURL'],
                    None,
                    self._ctx['IBMDBCLIDRIVER_INSTALL_DIR'],
                    self._ctx[clidriverpart.upper() + '_DLFILE'],
                    True)

        self._compilationEnv['IBM_DB_HOME'] = self._ctx['IBMDBCLIDRIVER_INSTALL_DIR']
        self._logMsg ('Installed IBMDB CLI Drivers to ' + self._ctx['IBMDBCLIDRIVER_INSTALL_DIR'])
        self._logMsg('-- Installed IBM DB CLI Drivers ------------------')

    def install_phpsource(self):
        self._logMsg('-- Downloading PHP Source ------------------------')
        self._install_direct(
                self._ctx['PHPSOURCE_DLURL'],
                None,
                self._ctx['PHPSOURCE_INSTALL_DIR'],
                self._ctx['PHPSOURCE_DLFILE'],
                True)

        self._cfPHPConfigPrefixDir = self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'],
                                            [self._phpBuildConfigFpath, '--prefix']).strip()
        cfPHPConfigLibDir = os.path.join(self._cfPHPConfigPrefixDir, 'lib')
        cfPHPConfigIncludeDir = os.path.join(self._cfPHPConfigPrefixDir, 'include')

        self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'], ['mkdir', '-p', self._cfPHPConfigPrefixDir])
        self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'], ['mkdir', '-p', cfPHPConfigLibDir])
        self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'], ['mkdir', '-p', cfPHPConfigIncludeDir])

        self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'],
                     ['cp', '-rf', self._ctx['PHPSOURCE_INSTALL_DIR'], cfPHPConfigIncludeDir])
        self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'],
                     ['cp', '-rf', self._ctx['PHPSOURCE_INSTALL_DIR'], cfPHPConfigLibDir])
        self._runCmd(self._compilationEnv, os.path.join(cfPHPConfigLibDir, 'php'),
                     ['cp', '-rf', 'acinclude.m4 Makefile.global config.sub config.guess ltmain.sh run-tests*.php',
                      os.path.join(cfPHPConfigLibDir, 'php', 'build')])
        self._runCmd(self._compilationEnv, os.path.join(cfPHPConfigLibDir, 'php', 'scripts'),
                     ['cp', '-rf', 'phpize.m4', os.path.join(cfPHPConfigLibDir, 'php', 'build')])
        self._runCmd(self._compilationEnv, os.path.join(cfPHPConfigIncludeDir, 'php'), ['./configure'])

        self._logMsg ('Downloaded PHP ' + self._ctx['PHPSOURCE_VERSION'] + ' source files')
        self._logMsg('-- Downloaded PHP Source -------------------------')

    def download_extensions(self):
        self._logMsg('-- Downloading IBM DB Extensions -----------------')
        for ibmdbExtn in ['IBM_DB2', 'PDO_IBM']:
            ibmdbExtnDownloadDir = self._ctx[ibmdbExtn + '_DLDIR']
            self._install_direct(
                self._ctx[ibmdbExtn + '_DLURL'],
                None,
                ibmdbExtnDownloadDir,
                self._ctx[ibmdbExtn + '_DLFILE'],
                True)
            self._runCmd(self._compilationEnv, self._ctx['BUILD_DIR'],
                 ['mv', os.path.join(ibmdbExtnDownloadDir,  self._zendModuleApiNo, ibmdbExtn.lower() + '.so'),
                  self._phpExtnDpath])
            self._logMsg ('Installed ' + ibmdbExtn)
        self._logMsg('-- Downloaded IBM DB Extensions ------------------')

    def cleanup(self):
        self._logMsg('-- Some House-keeping ----------------------------')
        self._runCmd(os.environ, self._ctx['BUILD_DIR'], ['rm', '-rf', self._ctx['DOWNLOAD_DIR']])
        self._logMsg('-- House-keeping Done ----------------------------')

IBMDBInstaller.register(__name__)

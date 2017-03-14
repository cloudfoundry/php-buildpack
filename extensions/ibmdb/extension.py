import logging
import os
import StringIO
from urlparse import urlparse
from build_pack_utils import stream_output
from build_pack_utils import utils
from extension_helpers import ExtensionHelper

PKGDOWNLOADS =  {
    'IBMDBCLIDRIVER_VERSION': '11.1',
    #'IBMDBCLIDRIVER_REPOSITORY': 'https://public.dhe.ibm.com/ibmdl/export/pub/software/data/db2/drivers/odbc_cli',
    #'IBMDBCLIDRIVER1_DLFILE': 'linuxx64_odbc_cli.tar.gz',
    #'IBMDBCLIDRIVER1_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/{IBMDBCLIDRIVER_DLFILE}',
    #'IBMDBCLIDRIVER2_DLFILE': '',    # intentionally left blank
    #'IBMDBCLIDRIVER2_DLURL': '',     # intentionally left blank
    'IBMDBCLIDRIVER_REPOSITORY': 'https://github.com/fishfin/ibmdb-php-extensions-linuxx64',
    'IBMDBCLIDRIVER1_DLFILE': 'ibm_data_server_driver_for_odbc_cli_linuxx64_v{IBMDBCLIDRIVER_VERSION}_1of2.tar.gz',
    'IBMDBCLIDRIVER1_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/raw/master/{IBMDBCLIDRIVER1_DLFILE}',
    'IBMDBCLIDRIVER2_DLFILE': 'ibm_data_server_driver_for_odbc_cli_linuxx64_v{IBMDBCLIDRIVER_VERSION}_2of2.tar.gz',
    'IBMDBCLIDRIVER2_DLURL': '{IBMDBCLIDRIVER_REPOSITORY}/raw/master/{IBMDBCLIDRIVER2_DLFILE}',

    'IBM_DB2_VERSION': '1.9.9',
    'IBM_DB2_REPOSITORY': 'https://github.com/fishfin/ibmdb-php-extensions-linuxx64',
    'IBM_DB2_DLFILE': 'ibm_db2-v{IBM_DB2_VERSION}.tar.gz',
    'IBM_DB2_DLURL': '{IBM_DB2_REPOSITORY}/raw/master/{IBM_DB2_DLFILE}',

    'PDO_IBM_VERSION': '1.3.4',
    'PDO_IBM_REPOSITORY': 'https://github.com/fishfin/ibmdb-php-extensions-linuxx64',
    'PDO_IBM_DLFILE': 'pdo_ibm-v{PDO_IBM_VERSION}.tar.gz',
    'PDO_IBM_DLURL': '{PDO_IBM_REPOSITORY}/raw/master/{PDO_IBM_DLFILE}',
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

        self._ibmdbClidriverBaseDir = 'ibmdb_clidriver'
        self._phpBuildRootDpath = os.path.join(self._ctx['BUILD_DIR'], 'php')
        self._phpBuildIniFpath = os.path.join(self._phpBuildRootDpath, 'etc', 'php.ini')

    def _defaults(self):
        pkgdownloads = PKGDOWNLOADS
        pkgdownloads['COMPILATION_DIR'] = os.path.join(self._ctx['BUILD_DIR'], '.build_ibmdb_extension')
        pkgdownloads['DOWNLOAD_DIR'] = os.path.join('{COMPILATION_DIR}', '.downloads')        
        pkgdownloads['IBMDBCLIDRIVER_INSTALL_DIR'] = os.path.join(self._ctx['BUILD_DIR'], 'ibmdb_clidriver')
        pkgdownloads['PHPSOURCE_INSTALL_DIR'] = os.path.join('{COMPILATION_DIR}', 'php')
        pkgdownloads['IBM_DB2_DLDIR'] = os.path.join('{PHPSOURCE_INSTALL_DIR}', 'ext', 'ibm_db2')
        pkgdownloads['PDO_IBM_DLDIR'] = os.path.join('{PHPSOURCE_INSTALL_DIR}', 'ext', 'pdo_ibm')
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

        self._phpExtnDir = self.findPhpExtnBaseDir()
        self._zendModuleApiNo = self._phpExtnDir[len(self._phpExtnDir)-8:]
        self._phpExtnDpath = os.path.join(self._phpBuildRootDpath, 'lib', 'php', 'extensions', self._phpExtnDir)

        self.install_clidriver()
        self.download_extensions()
        self.modifyPhpIni()
        self.cleanup()
        return 0

    def _service_environment(self):
        self._log.info(__file__ + "->service_environment")
        env = {
            #'IBM_DB_HOME': '$IBM_DB_HOME:$HOME/' + self._ibmdbClidriverBaseDir + '/lib',
            'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:$HOME/' + self._ibmdbClidriverBaseDir + '/lib',
            'PATH': '$HOME/' + self._ibmdbClidriverBaseDir + '/bin:$HOME/' 
                    + self._ibmdbClidriverBaseDir + '/adm:$PATH',
        }
        return env

    def _logMsg(self, logMsg):
        self._log.info(logMsg)
        print logMsg        

    def _install_direct(self, url, hsh, installDir, fileName=None, strip=False, extract=True):
        if not fileName:
            fileName = urlparse(url).path.split('/')[-1]
        fileToInstall = os.path.join(self._ctx['TMPDIR'], fileName)
        self._runCmd(os.environ, self._ctx['BUILD_DIR'], ['rm', '-rf', fileToInstall])
        self._installer._dwn.custom_extension_download(url, url, fileToInstall)

        if extract:
            return self._installer._unzipUtil.extract(fileToInstall, installDir, strip)
        else:
            shutil.copy(fileToInstall, installDir)
            return installDir

    def _runCmd(self, environ, currWorkDir, cmd, displayRunLog=False):
        stringioWriter = StringIO.StringIO()
        try:
            stream_output(stringioWriter, ' '.join(cmd), env=environ, cwd=currWorkDir, shell=True)
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
        with open(self._phpBuildIniFpath, 'wt') as phpIni:
            for line in lines:
                phpIni.write(line)

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
        self._logMsg('-- Installed IBM DB CLI Drivers ------------------')

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
                 ['cp', os.path.join(ibmdbExtnDownloadDir,  self._zendModuleApiNo, ibmdbExtn.lower() + '.so'),
                  self._phpExtnDpath])
            self._logMsg ('Installed extension ' + ibmdbExtn)
        self._logMsg('-- Downloaded IBM DB Extensions ------------------')

    def cleanup(self):
        self._logMsg('-- Some House-keeping ----------------------------')
        self._runCmd(os.environ, self._ctx['BUILD_DIR'], ['rm', '-rf', self._ctx['COMPILATION_DIR']])
        self._logMsg('-- House-keeping Done ----------------------------')

IBMDBInstaller.register(__name__)

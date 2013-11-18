import os
import gzip
import bz2
import zipfile
import shutil
from functools import partial
from subprocess import Popen
from subprocess import PIPE


class UnzipUtil(object):

    def __init__(self, config):
        self._ctx = config

    def _unzip(self, zipFile, intoDir, strip):
        tmpDir = (strip) and self._ctx['TEMP_DIR'] or intoDir
        zipIn = None
        try:
            zipIn = zipfile.ZipFile(zipFile, 'r')
            zipIn.extractall(tmpDir)
            if strip:
                members = zipIn.namelist()
                if len(members) > 0:
                    firstDir = members[0].split('/')[0]
                    moveFrom = os.path.join(tmpDir, firstDir)
                    if os.path.exists(moveFrom):
                        for item in os.listdir(moveFrom):
                            shutil.move(os.path.join(moveFrom, item),
                                        intoDir)
        finally:
            if zipIn:
                zipIn.close()
        return intoDir

    def _gunzip(self, zipFile, intoDir, strip):
        path = os.path.join(intoDir, os.path.basename(zipFile)[:-3])
        zipIn = None
        try:
            zipIn = gzip.open(zipFile, 'rb')
            with open(path, 'wb') as zipOut:
                for buf in iter(partial(zipIn.read, 8196), ''):
                    zipOut.write(buf)
        finally:
            if zipIn:
                zipIn.close()
        return path

    def _bunzip2(self, zipFile, intoDir, strip):
        path = os.path.join(intoDir, os.path.basename(zipFile)[:-4])
        zipIn = None
        try:
            zipIn = bz2.BZ2File(zipFile, 'rb')
            with open(path, 'wb') as zipOut:
                for buf in iter(partial(zipIn.read, 8196), ''):
                    zipOut.write(buf)
        finally:
            if zipIn:
                zipIn.close()
        return path

    def _tar_bunzip2(self, zipFile, intoDir, strip):
        return self._tar_helper(zipFile, intoDir, 'bz2', strip)

    def _tar_gunzip(self, zipFile, intoDir, strip):
        return self._tar_helper(zipFile, intoDir, 'gz', strip)

    def _untar(self, zipFile, intoDir, strip):
        return self._tar_helper(zipFile, intoDir, None, strip)

    def _tar_helper(self, zipFile, intoDir, compression, strip):
        # build command
        cmd = []
        if compression == 'gz':
            cmd.append('gunzip -c %s' % zipFile)
        elif compression == 'bz2':
            cmd.append('bunzip2 -c %s' % zipFile)
        if strip > 0:
            if compression is None:
                cmd.append('tar xf %s --strip-components %d'
                           % (zipFile, strip))
            else:
                cmd.append('tar xf - --strip-components %d' % strip)
        else:
            if compression is None:
                cmd.append('tar xf %s' % zipFile)
            else:
                cmd.append('tar xf -')
        command = (len(cmd) > 1) and ' | '.join(cmd) or ''.join(cmd)
        # run it
        cwd = os.getcwd()
        try:
            if not os.path.exists(intoDir):
                os.makedirs(intoDir)
            os.chdir(intoDir)
            if os.path.exists(zipFile):
                proc = Popen(command, stdout=PIPE, shell=True)
                output, unused_err = proc.communicate()
                retcode = proc.poll()
                if retcode:
                    raise RuntimeError("Extracting [%s] failed with code [%d]"
                                       % (zipFile, retcode))
        finally:
            os.chdir(cwd)
        return intoDir

    def _pick_based_on_file_extension(self, zipFile):
        if zipFile.endswith('.tar.gz') or zipFile.endswith('.tgz'):
            return self._tar_gunzip
        if zipFile.endswith('.tar.bz2'):
            return self._tar_bunzip2
        if zipFile.endswith('.tar'):
            return self._untar
        if zipFile.endswith('.gz'):
            return self._gunzip
        if zipFile.endswith('.bz2'):
            return self._bunzip2
        if zipFile.endswith('.zip') and zipfile.is_zipfile(zipFile):
            return self._unzip

    def extract(self, zipFile, intoDir, strip=False, method=None):
        if not method:
            method = self._pick_based_on_file_extension(zipFile)
        return method(zipFile, intoDir, strip)

import hashlib
import logging
from functools import partial
from subprocess import Popen
from subprocess import PIPE


class HashUtil(object):

    def __init__(self, config):
        self._ctx = config
        self._log = logging.getLogger('hashes')

    def calculate_hash(self, checkFile):
        if checkFile is None or checkFile == '':
            return ''
        hsh = hashlib.new(self._ctx['CACHE_HASH_ALGORITHM'])
        with open(checkFile, 'rb') as fileIn:
            for buf in iter(partial(fileIn.read, 8196), ''):
                hsh.update(buf)
        digest = hsh.hexdigest()
        self._log.debug("Hash of [%s] is [%s]", checkFile, digest)
        return digest

    def does_hash_match(self, digest, toFile):
        return (digest.split()[0] == self.calculate_hash(toFile))


class ShaHashUtil(HashUtil):

    def __init__(self, config):
        HashUtil.__init__(self, config)

    def calculate_hash(self, checkFile):
        if checkFile is None or checkFile == '':
            return ''
        proc = Popen(["shasum", "-b",
                      "-a", self._ctx['CACHE_HASH_ALGORITHM'].lstrip('sha'),
                      checkFile], stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate()
        retcode = proc.poll()
        if retcode == 0:
            digest = output.strip().split(' ')[0]
            self._log.debug("Hash of [%s] is [%s]", checkFile, digest)
            return digest
        elif retcode == 1:
            raise ValueError(err.split('\n')[0])

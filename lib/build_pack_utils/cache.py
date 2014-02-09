import os
import shutil
import logging
from hashes import HashUtil
from hashes import ShaHashUtil


class BaseCacheManager(object):

    def __init__(self, ctx):
        self._log = logging.getLogger('cache')
        if ctx.get('USE_EXTERNAL_HASH', False):
            self._log.debug("Using external hash.")
            self._hashUtil = ShaHashUtil(ctx)
        else:
            self._log.debug("Using hashlib.")
            self._hashUtil = HashUtil(ctx)

    def get(self, key, digest):
        return None

    def put(self, key, fileToCache):
        pass

    def delete(self, key):
        pass

    def exists(self, key, digest):
        return False


class DirectoryCacheManager(BaseCacheManager):

    def __init__(self, ctx):
        BaseCacheManager.__init__(self, ctx)
        self._baseDir = ctx.get('FILE_CACHE_BASE_DIRECTORY',
                                ctx['CACHE_DIR'])
        self._log.info("Using [%s] as cache directory.", self._baseDir)
        if not os.path.exists(self._baseDir):
            os.makedirs(self._baseDir)

    def get(self, key, digest):
        path = os.path.join(self._baseDir, key)
        if self.exists(key, digest):
            self._log.debug('Cache hit (%s, %s)', key, digest)
            return path

    def put(self, key, fileToCache, digest):
        path = os.path.join(self._baseDir, key)
        if (os.path.exists(path) and
                not self._hashUtil.does_hash_match(digest, path)):
            self._log.warning(
                "File [%s] already exists in the cache, but the digest "
                "[%s] does not match.  Will update the cache if the "
                "underlying file system supports it.", key, digest)
        shutil.copy(fileToCache, path)
        return path

    def delete(self, key):
        path = os.path.join(self._baseDir, key)
        if os.path.exists(path):
            self._log.warning(
                "You are trying to delete a file from the cache "
                "this is not supported for all file systems.")
            os.remove(path)

    def exists(self, key, digest):
        path = os.path.join(self._baseDir, key)
        return (os.path.exists(path) and
                self._hashUtil.does_hash_match(digest, path))

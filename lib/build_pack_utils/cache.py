import os
import shutil
from hashes import HashUtil
from hashes import ShaHashUtil


class BaseCacheManager(object):

    def __init__(self, ctx):
        if ctx.get('USE_EXTERNAL_HASH', False):
            self._hashUtil = ShaHashUtil(ctx)
        else:
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
        if not os.path.exists(self._baseDir):
            os.makedirs(self._baseDir)

    def get(self, key, digest):
        path = os.path.join(self._baseDir, key)
        if self.exists(key, digest):
            return path

    def put(self, key, fileToCache, digest):
        path = os.path.join(self._baseDir, key)
        if (os.path.exists(path) and
                not self._hashUtil.does_hash_match(digest, path)):
            print "File already exists in the cache, but the digest " \
                  "does not match.  Will update the cache if the " \
                  "underlying file system supports it."
        shutil.copy(fileToCache, path)
        return path

    def delete(self, key):
        path = os.path.join(self._baseDir, key)
        if os.path.exists(path):
            print "You are trying to delete a file from the cache " \
                  "this is not supported for all file systems."
        os.remove(path)

    def exists(self, key, digest):
        path = os.path.join(self._baseDir, key)
        return (os.path.exists(path) and
                self._hashUtil.does_hash_match(digest, path))

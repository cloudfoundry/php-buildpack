import urllib2
import re
import logging
from subprocess import Popen
from subprocess import PIPE


class Downloader(object):

    def __init__(self, config):
        self._ctx = config
        self._log = logging.getLogger('downloads')

    def download(self, url, toFile):
        res = urllib2.urlopen(url)
        with open(toFile, 'w') as f:
            f.write(res.read())
        print 'Downloaded [%s] to [%s]' % (url, toFile)
        self._log.info('Downloaded [%s] to [%s]', url, toFile)

    def download_direct(self, url):
        buf = urllib2.urlopen(url).read()
        self._log.info('Downloaded [%s] to memory', url)
        self._log.debug("Downloaded [%s] [%s]", url, buf)
        return buf


class CurlDownloader(object):

    def __init__(self, config):
        self._ctx = config
        self._status_pattern = re.compile(r'^(.*)<!-- Status: (\d+) -->$',
                                          re.DOTALL)
        self._log = logging.getLogger('downloads')

    def download(self, url, toFile):
        self._log.debug("Running [curl -s -o %s -w %%{http_code} %s]",
                        toFile, url)
        proc = Popen(["curl", "-s",
                      "-o", toFile,
                      "-w", '%{http_code}',
                      url], stdout=PIPE)
        output, unused_err = proc.communicate()
        proc.poll()
        self._log.debug("Curl returned [%s]", output)
        if output and \
                (output.startswith('4') or
                 output.startswith('5')):
            raise RuntimeError("curl says [%s]" % output)
        print 'Downloaded [%s] to [%s]' % (url, toFile)
        self._log.info('Downloaded [%s] to [%s]', url, toFile)

    def download_direct(self, url):
        self._log.debug(
            "Running [curl -s -w '<!-- Status: %%{http_code} -->' %s", url)
        proc = Popen(["curl", "-s",
                      "-w", '<!-- Status: %{http_code} -->',
                      url], stdout=PIPE)
        output, unused_err = proc.communicate()
        proc.poll()
        m = self._status_pattern.match(output)
        if m:
            resp = m.group(1)
            code = m.group(2)
            self._log.debug("Curl returned [%s]", code)
            if (code.startswith('4') or code.startswith('5')):
                raise RuntimeError("curl says [%s]" % output)
            self._log.info('Downloaded [%s] to memory', url)
            self._log.debug('Downloaded [%s] [%s]', url, resp)
            return resp

import urllib2
import re
from subprocess import Popen
from subprocess import PIPE


class Downloader(object):

    def __init__(self, config):
        self._ctx = config

    def download(self, url, toFile):
        res = urllib2.urlopen(url)
        with open(toFile, 'w') as f:
            f.write(res.read())
        print 'Downloaded [%s] to [%s]' % (url, toFile)

    def download_direct(self, url):
        return urllib2.urlopen(url).read()


class CurlDownloader(object):

    def __init__(self, config):
        self._ctx = config
        self._status_pattern = re.compile(r'^(.*)<!-- Status: (\d+) -->$',
                                          re.DOTALL)

    def download(self, url, toFile):
        proc = Popen(["curl", "-s",
                      "-o", toFile,
                      "-w", '%{http_code}',
                      url], stdout=PIPE)
        output, unused_err = proc.communicate()
        proc.poll()
        if output and \
                (output.startswith('4') or
                 output.startswith('5')):
            raise RuntimeError("curl says [%s]" % output)
        print 'Downloaded [%s] to [%s]' % (url, toFile)
    
    def download_direct(self, url):
        proc = Popen(["curl", "-s",
                      "-w", '<!-- Status: %{http_code} -->',
                      url], stdout=PIPE)
        output, unused_err = proc.communicate()
        proc.poll()
        m = self._status_pattern.match(output)
        if m:
            resp = m.group(1)
            code = m.group(2)
            if (code.startswith('4') or code.startswith('5')):
                raise RuntimeError("curl says [%s]" % output)
            return resp

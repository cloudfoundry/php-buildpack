import os
import re
import logging
from itertools import chain


class BaseFileSearch(object):
    def __init__(self):
        self._log = logging.getLogger('detecter')
        self.recursive = False
        self.fullPath = False

    def _match(self, term):
        return True

    def search(self, root):
        if self.recursive:
            self._log.debug("Recursively search [%s]", root)
            for head, dirs, files in os.walk(root):
                for name in chain(dirs, files):
                    if self.fullPath:
                        name = os.path.join(head, name)
                    if self._match(name):
                        self._log.debug("File [%s] matched.", name)
                        return True
                    self._log.debug("File [%s] didn't match.", name)
            return False
        else:
            self._log.debug("Searching [%s]", root)
            for name in os.listdir(root):
                if self.fullPath:
                    name = os.path.join(root, name)
                if self._match(name):
                    self._log.debug("File [%s] matched.", name)
                    return True
                self._log.debug("File [%s] didn't match.", name)


class TextFileSearch(BaseFileSearch):
    def __init__(self, text):
        BaseFileSearch.__init__(self)
        self._text = text

    def _match(self, term):
        if self._text:
            return term == self._text


class RegexFileSearch(BaseFileSearch):
    def __init__(self, regex):
        BaseFileSearch.__init__(self)
        if hasattr(regex, 'strip'):
            self._regex = re.compile(regex)
        else:
            self._regex = regex

    def _match(self, term):
        if self._regex:
            return (self._regex.match(term) is not None)


class StartsWithFileSearch(BaseFileSearch):
    def __init__(self, start):
        BaseFileSearch.__init__(self)
        self._start = start

    def _match(self, term):
        if self._start:
            return term.startswith(self._start)


class EndsWithFileSearch(BaseFileSearch):
    def __init__(self, end):
        BaseFileSearch.__init__(self)
        self._end = end

    def _match(self, term):
        if self._end:
            return term.endswith(self._end)


class ContainsFileSearch(BaseFileSearch):
    def __init__(self, contains):
        BaseFileSearch.__init__(self)
        self._contains = contains

    def _match(self, term):
        if self._contains:
            return term.find(self._contains) >= 0

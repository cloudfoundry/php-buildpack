# -*- coding:utf-8 -*-

import os
import sys

from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''

install_requires=[
    'setuptools',
    ]

docs_extras = [
    ]

tests_require =[
    "pytest"
]
testing_extras = tests_require + [
    ]

from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        import pytest
        pytest.main(self.test_args)


setup(name='semver',
      version='0.1',
      description='port of node-semver',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        'Programming Language :: Python :: 3', 
        "Programming Language :: Python :: Implementation :: CPython",
        ],
      keywords='version semver',
      author="",
      author_email="",
      url="https://github.com/podhmo/python-semver",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      extras_require = {
          'testing':testing_extras,
          'docs':docs_extras,
          },
      tests_require = tests_require,
      cmdclass = {'test': PyTest},
      entry_points = """      """,
      license="mit",
      )

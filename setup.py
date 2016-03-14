#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import ast
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

_version_re = re.compile(r'VERSION\s+=\s+(.*)')

MINOR_VERSION = 2

with open('lizzy/version.py', 'rb') as f:
    version_content = f.read().decode('utf-8')
    VERSION = ast.literal_eval(_version_re.search(version_content).group(1))


def get_long_description():
    """
    Read long description in a way that doesn't break if README.rst doesn't exist (for example in the docker image)
    """
    try:
        description = open('README.rst').read()
    except FileNotFoundError:
        description = ''
    return description


class PyTest(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None
        self.pytest_args = ['--cov', 'lizzy', '--cov-report', 'term-missing', '-v']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='lizzy',
    packages=find_packages(),
    version='{}.{}'.format(VERSION, MINOR_VERSION),
    description='REST Service to deploy AWS CF templates using Senza',
    long_description=get_long_description(),
    author='Zalando SE',
    url='https://github.com/zalando/lizzy',
    license='Apache License Version 2.0',
    install_requires=['connexion>=0.13',
                      'environmental>=1.1',
                      'decorator',
                      'pystache',
                      'pytz',
                      'pyyaml',
                      'rod',
                      'stups-kio',
                      'stups-senza>=1.0.40',
                      'uwsgi',
                      'uwsgi_metrics3'],
    tests_require=['pytest-cov', 'pytest'],
    cmdclass={'test': PyTest},
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    include_package_data=True,
    package_data={'lizzy': ['swagger/*']},  # include swagger specs
)

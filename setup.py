#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# The minor and major versions should match lizzy's version
VERSION_MAJOR = 1
VERSION_MINOR = 4
REVISION = 0
VERSION = '{VERSION_MAJOR}.{VERSION_MINOR}.{REVISION}'.format_map(locals())


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
    version=VERSION,
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
                      'stups-senza',
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

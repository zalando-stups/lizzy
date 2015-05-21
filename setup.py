#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys

from distutils import log as logger
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand


VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION = '{VERSION_MAJOR}.{VERSION_MINOR}'.format_map(locals())


def get_long_description():
    """
    Read long description in a way that doesn't break if README.rst doesn't exist (for example in the docker image)
    """
    try:
        description = open('README.rst').read()
    except FileNotFoundError:
        description = ''
    return description


# TODO move this to a new package
class Dockerize(Command):
    """Build."""

    user_options = [('tag=', 't', 'docker image tag')]

    def initialize_options(self):
        self.tag = None

    def finalize_options(self):
        pass

    def run(self):
        # TODO error handling on subprocesses
        logger.info('Making Wheel')
        self.run_command('bdist_wheel')
        logger.info('Making Wheels for dependencies')
        pip = subprocess.Popen(['pip3', 'wheel', '.'])
        pip.wait()
        logger.info('Building docker')
        docker_cmd = ['docker', 'build', '--pull', '--no-cache']
        if self.tag:
            docker_cmd.extend(['--tag', self.tag])
        docker_cmd.append('.')
        docker_build = subprocess.Popen(docker_cmd)
        docker_build.wait()


class PyTest(TestCommand):

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None
        self.pytest_args = ['--cov', 'environmental', '--cov-report', 'term-missing']

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
    install_requires=['APScheduler', 'connexion', 'environmental', 'pyyaml', 'rod', 'stups-senza'],
    tests_require=['pytest-cov', 'pytest'],
    cmdclass={'docker': Dockerize,
              'test': PyTest},
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

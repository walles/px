#!/usr/bin/env python

import subprocess

from setuptools import setup

setup(
    name='px',
    version=subprocess.check_output(['git', 'describe', '--dirty']).strip(),
    description='Cross Functional Process Explorer',
    author='Johan Walles',
    author_email='walles@gmail.com',
    url='https://github.com/walles/px',
    license='MIT',

    packages=['px'],

    install_requires=[
        'docopt == 0.6.2',
        'python-dateutil == 2.5.0',
        ],

    setup_requires=[
        'pytest-runner'
        ],

    tests_require=[
        'pytest',
        ],

    entry_points={
        'console_scripts': [
            'px = px.px:main',
        ],
    }
)

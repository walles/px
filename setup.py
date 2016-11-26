#!/usr/bin/env python

from setuptools import setup

setup(
    name='px',
    version='0.4.3',  # FIXME: Set from git describe --dirty
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

import io
import os
import sys
import glob
import re
import requests
from shutil import rmtree

from setuptools import find_packages, setup, Command
from setuptools.command import build_py

# Package meta-data.
NAME = 'logpresso'
DESCRIPTION = 'Python SDK for Logpresso'
URL = 'https://github.com/logpresso/pylogpresso'
EMAIL = 'wghwang@eediom.com'
AUTHOR = 'Won Gune Hwang'
REQUIRES_PYTHON = '>=2.7.0,>=3.6.0'
VERSION = None

# What packages are required for this module to be executed?
REQUIRED = [
    'future', 'pyjnius'
]

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION

CLIENT_VER = ''
try:
    globbed = glob.glob('logpresso/araqne-logdb-client*-package.jar')[0]
    print('globbed', globbed)
    CLIENT_VER = re.search(r'logpresso/araqne-logdb-client-(.*)-package\.jar', globbed).group(1)
    print('client-ver', CLIENT_VER)
except Exception:
    pass

class DownloadLogpressoClientCommand(Command):
    """Support setup.py download."""

    description = 'download araqne-logdb-client'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Downloading araqne-logdb-client JAR')
        ver = '1.7.1'
        filename = 'araqne-logdb-client-{0}-package.jar'.format(ver)
        r = requests.get('http://staging.araqne.org/org/araqne/araqne-logdb-client/{0}/{1}'.format(ver, filename))
        open('logpresso/' + filename, 'wb').write(r.content)

        CLIENT_VER = ver
        
        sys.exit()

class BuildPyCommand(build_py.build_py):
    def run(self):
        if not CLIENT_VER:
            raise Exception('cannot find araqne-logdb-client jar')
        super().run(self)

# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],

    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    include_package_data=True,
    license='Apache',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    # $ setup.py publish support.
    cmdclass={
        'download': DownloadLogpressoClientCommand,
    },
    package_data={
        'logpresso': ['araqne-logdb-client-'+CLIENT_VER+'-package.jar']
    }
)

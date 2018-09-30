#!/usr/bin/env python
__usage__ = "setup.py command [--options]"
__description__ = "standard install script"
__author__ = "Reed Essick (reed.essick@gmail.com)"

#-------------------------------------------------

from distutils.core import setup
import glob
import os.path

setup(
    name = 'autorestart',
    version = '0.0',
    url = 'https://github.com/reedessick/autorestart',
    author = __author__,
    author_email = 'reed.essick@gmail.com',
    description = __description__,
    license = 'MIT',
    scripts = [
        'bin/autorestart',            ### batch pipeline scripts
    ],
    packages = [
        'autorestart',
    ],
    data_files = [],
    requires = [],
)

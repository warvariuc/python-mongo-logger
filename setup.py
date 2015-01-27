#!/usr/bin/env python
import os
import imp

import setuptools
import pip.req


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VERSION_FILE_PATH = os.path.join(BASE_DIR, 'mongologger/_version.py')
_version = imp.load_source('_version', VERSION_FILE_PATH)

REQUIREMENTS_FILE_PATH = os.path.join(BASE_DIR, 'requirements.txt')
requirements = [str(ir.req) for ir in pip.req.parse_requirements(REQUIREMENTS_FILE_PATH)]

setuptools.setup(
    name='mongologger',
    version=_version.__version__,
    description=('This module creates a logger ``mongologger`` which once enabled logs all queries '
                 'to MongoDB.'),
    url='https://github.com/warvariuc/python-mongo-logger',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
    ],
    platforms='any',
    packages=setuptools.find_packages(),
    include_package_data=True,  # use MANIFEST.in during install
    zip_safe=False,
    install_requires=requirements,
)

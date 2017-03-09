#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from netspryte import __version__, __author__, __email__

try:
    from setuptools import setup, find_packages
except ImportError:
    print("netspryte needs setuptools to build")
    sys.exit(1)

setup(name='netspryte',
      version=__version__,
      author=__author__,
      author_email=__email__,
      license='GPLv3',
      install_requires=[
          'flask',
          'peewee',
          'psycopg2',
          'pysnmp',
          ],
      package_dir={'' : 'lib'},
      packages=find_packages('lib'),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Natural Language :: English',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Systems Administration',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Networking',
          'Topic :: Utilities',
      ],
      scripts=[
          'bin/netspryte-collect-snmp',
          'bin/netspryte-discover',
          'bin/netspryte-gen-graph.cgi',
          'bin/netspryte-mk-html',
          'bin/rrd-add-ds',
      ],
      data_files=[])

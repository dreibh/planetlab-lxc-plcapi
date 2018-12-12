#!/usr/bin/python
#
# Setup script for PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from distutils.core import setup
from glob import glob

setup(packages = ['PLC', 'PLC/Methods', 'PLC/Methods/system', 'PLC/Accessors'],
      scripts = ['plcsh', 'Server.py'],
      data_files = [
        ('', ['planetlab5.sql']),
        # package for mod_python and mod_wsgi, defer choice to myplc
        ('apache', ['apache/ModPython.py', 'apache/__init__.py', 'apache/plc.wsgi']),
        ('php', ['php/plc_api.php']),
        ('migrations', 
         ['migrations/README.txt',
          'migrations/extract-views.py'] 
         + glob('migrations/[0-9][0-9][0-9]*')),
        ('extensions', ['extensions/README.txt']),
        ])

#!/usr/bin/python
#
# Setup script for PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from distutils.core import setup
from glob import glob

setup(py_modules = ['ModPython'],
      packages = ['PLC', 'PLC/Methods', 'PLC/Methods/system', 'PLC/Accessors', 'PLC/Legacy'],
      scripts = ['plcsh', 'Server.py'],
      data_files = [
        ('', ['planetlab5.sql']),
        ('php', ['php/plc_api.php']),
        ('migrations', 
         ['migrations/README.txt',
          'migrations/extract-views.py'] 
         + glob('migrations/[0-9][0-9][0-9]*')),
        ('migrations/v4.2-to-4.3', 
         ['migrations/v4.2-to-4.3/migrate.sh',
          'migrations/v4.2-to-4.3/migrate.sed',
          'migrations/v4.2-to-4.3/migrate.sql',
          'migrations/v4.2-to-4.3/parse-site-nodegroups.py',
          'migrations/v4.2-to-4.3/site-nodegroups.def'
          ]),
        ])

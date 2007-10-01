#!/usr/bin/python
#
# Setup script for PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: setup.py 519 2007-06-12 14:36:25Z thierry $
#

from distutils.core import setup
from glob import glob

setup(py_modules = ['ModPython'],
      packages = ['PLC', 'PLC/Methods', 'PLC/Methods/system'],
      scripts = ['plcsh', 'Server.py'],
      data_files = [('', ['planetlab4.sql']),
                    ('php', ['php/plc_api.php']),
                    ('migrations', ['migrations/README.txt'] + glob('migrations/[0-9][0-9][0-9]*')),
                    ])

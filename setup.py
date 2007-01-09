#!/usr/bin/python
#
# Setup script for PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: setup.py,v 1.4 2006/10/27 20:08:46 mlhuang Exp $
#

from distutils.core import setup

setup(py_modules = ['ModPython'],
      packages = ['PLC', 'PLC/Methods', 'PLC/Methods/system'],
      scripts = ['plcsh', 'Server.py', 'Test.py'],
      data_files = [('', ['planetlab4.sql']),
                    ('php', ['php/plc_api.php'])])

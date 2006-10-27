#!/usr/bin/python
#
# Setup script for PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: setup.py,v 1.1 2006/10/27 18:54:21 mlhuang Exp $
#

from distutils.core import setup

setup(py_modules = ['ModPython'],
      packages = ['PLC', 'PLC/Methods'],
      scripts = ['Shell.py', 'Server.py', 'Test.py'],
      data_files = [('php', ['php/plc_api.php'])])

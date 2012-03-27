#!/usr/bin/python
#
# PLCAPI configuration store. Supports XML-based configuration file
# format exported by MyPLC.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2004-2006 The Trustees of Princeton University
#

import os
import sys

from PLC.Faults import *
from PLC.Debug import profile

# If we have been checked out into a directory at the same
# level as myplc, where plc_config.py lives. If we are in a
# MyPLC environment, plc_config.py has already been installed
# in site-packages.
myplc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + \
        os.sep + "myplc"

class Config:
    """
    Parse the bash/Python/PHP version of the configuration file. Very
    fast but no type conversions.
    """

    def __init__(self, file = "/etc/planetlab/plc_config"):
        # Load plc_config
        try:
            execfile(file, self.__dict__)
        except:
            # Try myplc directory
            try:
                execfile(myplc + os.sep + "plc_config", self.__dict__)
            except:
                raise PLCAPIError("Could not find plc_config in " + \
                                  file + ", " + \
                                  myplc + os.sep + "plc_config")

class XMLConfig:
    """
    Parse the XML configuration file directly. Takes longer but is
    presumably more accurate.
    """

    def __init__(self, file = "/etc/planetlab/plc_config.xml"):
        try:
            from plc_config import PLCConfiguration
        except:
            sys.path.append(myplc)
            from plc_config import PLCConfiguration

        # Load plc_config.xml
        try:
            cfg = PLCConfiguration(file)
        except:
            # Try myplc directory
            try:
                cfg = PLCConfiguration(myplc + os.sep + "plc_config.xml")
            except:
                raise PLCAPIError("Could not find plc_config.xml in " + \
                                  file + ", " + \
                                  myplc + os.sep + "plc_config.xml")

        for (category, variablelist) in cfg.variables().values():
            for variable in variablelist.values():
                # Try to cast each variable to an appropriate Python
                # type.
                if variable['type'] == "int":
                    value = int(variable['value'])
                elif variable['type'] == "double":
                    value = float(variable['value'])
                elif variable['type'] == "boolean":
                    if variable['value'] == "true":
                        value = True
                    else:
                        value = False
                else:
                    value = variable['value']

                # Variables are split into categories such as
                # "plc_api", "plc_db", etc. Within each category are
                # variables such as "host", "port", etc. For backward
                # compatibility, refer to variables by their shell
                # names.
                shell_name = category['id'].upper() + "_" + variable['id'].upper()
                setattr(self, shell_name, value)

if __name__ == '__main__':
    import pprint
    pprint = pprint.PrettyPrinter()
    pprint.pprint(Config().__dict__.items())

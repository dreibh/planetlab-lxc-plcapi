# Thierry Parmentelat - INRIA
# $Id$
#
# Shortcuts_site.py is the place where you can define your own tag accessors
# this will not be overwritten through rpm upgrades in a myplc-devel packaging
#
# methods denotes the set of methods (names) that get inserted into the API
# it is updated by define_accessors

methods=[]

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

#### example : attach vlan ids on interfaces
###define_accessors(current_module, Interface, "Vlan", "vlan","interface/general", "tag for setting VLAN id",
###                 get_roles=all_roles, set_roles=tech_roles)

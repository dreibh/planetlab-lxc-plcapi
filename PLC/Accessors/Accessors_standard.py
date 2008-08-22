# Thierry Parmentelat - INRIA
# $Id$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

# node architecture 
define_accessors(current_module, Node, "Arch", 'arch',  'node/config', 'architecture name', 
                 get_roles=all_roles, set_roles=tech_roles )

# node deployment (alpha, beta, ...)
define_accessors(current_module, Node, "Deployment", "deployment", "node/config", "deployment flavour",
                 get_roles=all_roles, set_roles=['admin'])

# interface alias
define_accessors(current_module, Interface, "Ifname", "ifname", "interface/config", "linux name",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Driver", "driver", "interface/config", "driver name",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Alias", "alias", "interface/config", "interface alias",
                 get_roles=all_roles, set_roles=tech_roles)

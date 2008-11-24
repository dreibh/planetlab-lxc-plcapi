# Thierry Parmentelat - INRIA
# $Id$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

# NOTE.
# most of these tag types are defined in MyPLC/db-config, so any details here in the 
# description/category area is unlikely to make it into the database
#

# slice vref
define_accessors(current_module, Slice, "Vref", 'vref', 'slice/config', 'vserver reference image type',
                 get_roles=all_roles, set_roles=['admin'])


# node architecture 
define_accessors(current_module, Node, "Arch", 'arch',  'node/config', 'architecture name', 
                 get_roles=all_roles, set_roles=tech_roles )
# distribution to be deployed
define_accessors(current_module, Node, "Pldistro", 'pldistro',  'node/config', 'PlanetLab distribution', 
                 get_roles=all_roles, set_roles=['admin'] )
# node deployment (alpha, beta, ...)
define_accessors(current_module, Node, "Deployment", "deployment", "node/operation", 
                 'deployment flavour, typically "alpha", "beta", or "production"',
                 get_roles=all_roles, set_roles=['admin'])
# extension
define_accessors(current_module, Node, "Extensions", "extensions", "node/config", "space-separated list of extensions to install",
                 get_roles=all_roles, set_roles=['admin'])
# test nodes perform their installation from an uncompressed bootstrapfs
define_accessors(current_module, Node, "PlainBoostrapfs", "plain-bootstrapfs", "node/config", "use uncompressed bootstrapfs when set",
                 get_roles=all_roles, set_roles=['admin','pi','tech']

# interface accessors
define_accessors(current_module, Interface, "Ifname", "ifname", "interface/config", "linux name",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Driver", "driver", "interface/config", "driver name",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Alias", "alias", "interface/config", "interface alias",
                 get_roles=all_roles, set_roles=tech_roles)

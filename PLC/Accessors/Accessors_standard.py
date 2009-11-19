# Thierry Parmentelat - INRIA
# $Id$
# $URL$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
#from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

# NOTE.
# most of these tag types are defined in MyPLC/db-config, so any details here in the 
# description/category area is unlikely to make it into the database
#

# slice vref
# xxx - don't expose yet in api interface and slices dont know how to use that yet
define_accessors(current_module, Slice, "Vref", "vref", 
                 "slice/config", "vserver reference image type",
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)


# node architecture 
define_accessors(current_module, Node, "Arch", "arch",  
                 "node/config", "architecture name", 
                 get_roles=all_roles, set_roles=tech_roles, expose_in_api=True)
# distribution to be deployed
define_accessors(current_module, Node, "Pldistro", "pldistro",
                 "node/config", "PlanetLab distribution", 
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)
# node deployment (alpha, beta, ...)
define_accessors(current_module, Node, "Deployment", "deployment",
                 "node/operation", 'typically "alpha", "beta", or "production"',
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)
# extension
define_accessors(current_module, Node, "Extensions", "extensions", 
                 "node/config", "space-separated list of extensions to install",
                 get_roles=all_roles, set_roles=["admin"],expose_in_api=True)
# test nodes perform their installation from an uncompressed bootstrapfs
define_accessors(current_module, Node, "PlainBootstrapfs", "plain-bootstrapfs", 
                 "node/config", "use uncompressed bootstrapfs when set",
                 get_roles=all_roles, set_roles=tech_roles)

# the tags considered when creating a boot CD
define_accessors(current_module, Node, "Serial", "serial",
                 "node/bootcd", "serial to use when creating the boot CD -- see GetBootMedium")
define_accessors(current_module, Node, "Cramfs", "cramfs",
                 "node/bootcd", "boot CD to use cramfs if set -- see GetBootMedium")
define_accessors(current_module, Node, "Kvariant", "kvariant",
                 "node/bootcd", "the variant to use for creating the boot CD -- see GetBootMedium")
define_accessors(current_module, Node, "Kargs", "kargs",
                 "node/bootcd", "extra args to pass the kernel on the Boot CD -- see GetBootMedium")
define_accessors(current_module, Node, "NoHangcheck", "no-hangcheck",
                 "node/bootcd", "disable hangcheck on the boot CD if set -- see GetBootMedium")

# interface 
# xxx - don't expose yet in api interface and slices dont know how to use that yet
define_accessors(current_module, Interface, "Ifname", "ifname", 
                 "interface/config", "linux name",
                 get_roles=all_roles, set_roles=tech_roles, expose_in_api=True)
define_accessors(current_module, Interface, "Driver", "driver", 
                 "interface/config", "driver name",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Alias", "alias", 
                 "interface/config", "interface alias",
                 get_roles=all_roles, set_roles=tech_roles)

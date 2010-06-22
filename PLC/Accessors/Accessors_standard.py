# Thierry Parmentelat - INRIA
# $Id$
# $URL$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Slices import Slice
from PLC.Sites import Site
from PLC.Persons import Person
#from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, admin_roles, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

# NOTE.
# The 'Get' and 'Set' accessors defined here automagically create the corresponding TagType in the database
# for safety, some crucial tags are forced to be created at plc startup time, through the db-config.d mechanism
# You might wish to keep this roughly in sync with db-config.d/011-standard_tags
#

#
### system slices - at least planetflow - still rely on 'vref'
#

# These following accessors are mostly of interest for implementing the
# GetSliceFamily method, that takes into account the vref attribute,
# as well as the 3 attributes below, and the PLC_FLAVOUR config category

### slice vref
define_accessors(current_module, Slice, "Vref", "vref",
                 "slice/config", "vserver reference image name",
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)

# xxx the accessor factory should enforce the category and descriptions provided here.
# and BTW the tag should be created right away as far as possible, or at least when a Get is issued
# also note that the two 'arch' instances use here will end in the same unique TagType object,
# so you should make sure to use the same category/description for both
define_accessors(current_module, Slice, "Arch", "arch",
                 "node/slice/config", "node arch or slivers arch",
                 get_roles=all_roles, set_roles=["user"], expose_in_api=True)
define_accessors(current_module, Slice, "Pldistro", "pldistro",
                 "node/slice/config", "PlanetLab distribution to use for node or slivers",
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)
define_accessors(current_module, Slice, "Fcdistro", "fcdistro",
                 "node/slice/config", "Fedora or CentOS distribution to use for node or slivers",
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)

# Ditto for the GetNodeFlavour method
define_accessors(current_module, Node, "Arch", "arch",
                 "node/slice/config", "node arch or slivers arch",
                 get_roles=all_roles, set_roles=tech_roles, expose_in_api=True)
define_accessors(current_module, Node, "Pldistro", "pldistro",
                 "node/slice/config", "PlanetLab distribution to use for node or slivers",
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)
define_accessors(current_module, Node, "Fcdistro", "fcdistro",
                 "node/slice/config", "Fedora or CentOS distribution to use for node or slivers",
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)
# node deployment (alpha, beta, ...)
define_accessors(current_module, Node, "Deployment", "deployment",
                 "node/operation", 'typically "alpha", "beta", or "production"',
                 get_roles=all_roles, set_roles=["admin"], expose_in_api=True)
# extension
define_accessors(current_module, Node, "Extensions", "extensions",
                 "node/config", "space-separated list of extensions to install",
                 get_roles=all_roles, set_roles=["admin"],expose_in_api=True)
# access HRN - this is the ideal definition of roles, even if AddNodeTag cannot handle this
define_accessors(current_module, Node, "Hrn","hrn",
                 "node/sfa", "SFA human readable name",
                 get_roles=all_roles, set_roles=["admin","pi","tech"], expose_in_api=True)

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
define_accessors(current_module, Interface, "Backdoor", "backdoor",
                 "interface/hidden", "For testing new settings",
                 get_roles=all_roles, set_roles=admin_roles)

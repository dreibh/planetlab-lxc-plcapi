#
# Thierry Parmentelat - INRIA
#
from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Sites import Site
from PLC.Persons import Person

from PLC.Accessors.Factory import define_accessors, admin_roles, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

# NOTE.
# The 'Get' and 'Set' accessors defined here automagically create the corresponding TagType in the database
# for safety, some crucial tags are forced to be created at plc startup time, through the db-config.d mechanism
#

# These following accessors are mostly of interest for implementing the
# The GetSliceFamily and GetNodeFlavour methods take into account various tags, 
# esp. arch, fcdistro, pldistro, vref (for slices) and deployment (for nodes)
# as well as the global PLC_FLAVOUR config category
# in order to return all configuration details for a given node or slice

### slice vref
define_accessors(current_module, Slice, "Vref", "vref",
                 "slice/config", "vserver reference image name",
                 set_roles=["admin","pi","user","node"], expose_in_api=True)
# this contains the actual script text
# if set, it supersedes 'initscript'
define_accessors(current_module, Slice, "InitscriptCode","initscript_code",
                 "slice/usertools", "Slice initialization script code",
                 set_roles=["admin","pi","user"], expose_in_api=True)
# this may contain a *name* that refers to the GetInitScripts
# it was initially designed to share scripts among slices
define_accessors(current_module, Slice, "Initscript","initscript",
                 "slice/usertools", "Slice initialization script name",
                 set_roles=["admin","pi","user"], expose_in_api=True)

# BootManager might need to set any of these 3, so 'node' needs to be in set_roles
# needs 'pi' and 'tech' for managing their node
# needs 'user' for managing their slices
# needs 'admin' so the Set method is accessible
define_accessors(current_module, [Slice,Node], "Arch", "arch",
                 "node/slice/config", "node arch or slivers arch",
                 set_roles=all_roles, expose_in_api=True)
define_accessors(current_module, [Slice,Node], "Pldistro", "pldistro",
                 "node/slice/config/sfa", "PlanetLab distribution to use for node or slivers",
                 set_roles=all_roles, expose_in_api=True)
# fc of course historically was for fedora core
define_accessors(current_module, [Slice,Node], "Fcdistro", "fcdistro",
                 "node/slice/config", "Linux distribution to use for node or slivers",
                 set_roles=all_roles, expose_in_api=True)

# the virtualization model to use - this is only used by the bootmanager for 
# picking the right options e.g. prior to reinstalling
# see PLC_FLAVOUR_VIRT_MAP to see how the default gets computed
define_accessors(current_module, Node, "Virt", "virt",
                 "node/operation", 'typically "vs" or "lxc"',
                 set_roles=all_roles, expose_in_api=True)
# node deployment (alpha, beta, ...)
define_accessors(current_module, Node, "Deployment", "deployment",
                 "node/operation", 'typically "alpha", "beta", or "production"',
                 set_roles=["admin"], expose_in_api=True)
# extensions - leave this to admin only until the semantics is made more clear
define_accessors(current_module, Node, "Extensions", "extensions",
                 "node/config", "space-separated list of extensions to install",
                 set_roles=["admin"],expose_in_api=True)
# access HRN - this is the ideal definition of roles, even if AddNodeTag cannot handle this
define_accessors(current_module, [Node,Person,Slice] , "Hrn", "hrn",
                 "node/person/slice/sfa", "SFA human readable name",
                 set_roles=all_roles, expose_in_api=True)

# test nodes perform their installation from an uncompressed bootstrapfs
define_accessors(current_module, Node, "PlainBootstrapfs", "plain-bootstrapfs",
                 "node/config", "use uncompressed bootstrapfs when set",
                 set_roles=tech_roles)

# the tags considered when creating a boot CD
define_accessors(current_module, Node, "Serial", "serial",
                 "node/bootcd", "serial to use when creating the boot CD -- see GetBootMedium",
                 set_roles=tech_roles)
define_accessors(current_module, Node, "Cramfs", "cramfs",
                 "node/bootcd", "boot CD to use cramfs if set -- see GetBootMedium",
                 set_roles=tech_roles)
define_accessors(current_module, Node, "Kvariant", "kvariant",
                 "node/bootcd", "the variant to use for creating the boot CD -- see GetBootMedium",
                 set_roles=tech_roles)
define_accessors(current_module, Node, "Kargs", "kargs",
                 "node/bootcd", "extra args to pass the kernel on the Boot CD -- see GetBootMedium",
                 set_roles=tech_roles)
define_accessors(current_module, Node, "NoHangcheck", "no-hangcheck",
                 "node/bootcd", "disable hangcheck on the boot CD if set -- see GetBootMedium",
                 set_roles=tech_roles)

# interface
# xxx - don't expose yet in api interface and slices dont know how to use that yet
define_accessors(current_module, Interface, "Ifname", "ifname",
                 "interface/config", "linux name",
                 set_roles=tech_roles, expose_in_api=True)
define_accessors(current_module, Interface, "Driver", "driver",
                 "interface/config", "driver name",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Alias", "alias",
                 "interface/config", "interface alias",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Backdoor", "backdoor",
                 "interface/hidden", "For testing new settings",
                 set_roles=admin_roles)

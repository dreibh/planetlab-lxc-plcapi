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

# this is how to request the features
define_accessors(current_module, Slice, "OmfControl","omf_control",
                 "slice/usertools","Pre-install and configure OMF Resource Controller in slice if set",
                 set_roles=all_roles, expose_in_api=True)


define_accessors(current_module, Slice, "SliverHMAC","enable_hmac",
                 "slice/usertools","Create HMAC keys for node in slice (slivers)",
                 set_roles=all_roles, expose_in_api=True)

# this is where the crypto stuff gets stored 
# this ends up in a sliver tag - the node creates that
# the accessors engine does not know how to create sliver accessors
# like e.g. GetSliverHmac(node,slice)
# but they are mentioned here as they are related to the above

# Security capability to empower a slice to make an authenticated API call, set by silverauth NM plugin.
define_accessors(current_module, Slice, "Hmac","hmac",
                 "slice/auth", "Sliver authorization key, for authenticated API call",
                 set_roles=['admin','node'])
# sliver-dependant ssh key, used to authenticate the experimental plane with OMF tools
define_accessors(current_module, Slice, "SshKey", "ssh_key",
                 'slice/auth', "Sliver public ssh key",
                 set_roles= ['admin','node'])

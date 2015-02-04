# Author:
# Guilherme Sperb Machado <gsm@machados.org> - UZH
# Created: 01/Aug/2014
# Last modified: 01/Sep/2014

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

#### IPv6 addr/prefix to distribute to slivers on the node!
define_accessors(current_module, Interface, "SliversIPv6Prefix", "sliversipv6prefix",
                 "interface/ipv6", "The IPv6 Range/Prefix for the Slivers",
                 set_roles=tech_roles)

#### IPv6 address assigned to the sliver of a particular node!
define_accessors(current_module, Slice, "IPv6Address", "ipv6_address",
                 "slice/usertools","IPv6 address assigned to the sliver in a particular node",
                 set_roles=all_roles, expose_in_api=True)


# Thierry Parmentelat - INRIA
# $Id: Accessors_standard.py 10295 2008-08-19 21:49:06Z thierry $

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles

import sys
current_module = sys.modules[__name__]

#### Wireless

define_accessors(current_module, Interface, "Mode", "wireless_mode", "interface/wireless", "wireless operation mode",
                 get_roles=all_roles, set_roles=tech_roles)

#["essid", "nw", "freq", "channel", "sens", "rate", "key", "key1", "key2", "key3", "key4", "securitymode", "iwconfig", "iwpriv" ]
#
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)
#define_accessors(current_module, Interface, "Xxx", "Xxx", "interface/wireless", "XXX",
#                 get_roles=all_roles, set_roles=tech_roles)


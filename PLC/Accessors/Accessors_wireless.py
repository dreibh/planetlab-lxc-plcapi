#
# Thierry Parmentelat - INRIA
#
from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

#### Wireless
define_accessors(current_module, Interface, "Mode", "mode",
                 "interface/wifi", "Wifi operation mode - see iwconfig",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Essid", "essid",
                 "interface/wifi", "Wireless essid - see iwconfig",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Nw", "nw",
                 "interface/wifi", "Wireless nw - see iwconfig",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Freq", "freq",
                 "interface/wifi", "Wireless freq - see iwconfig",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Channel", "channel",
                 "interface/wifi", "Wireless channel - see iwconfig",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Sens", "sens",
                 "interface/wifi", "Wireless sens - see iwconfig",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Rate", "rate",
                 "interface/wifi", "Wireless rate - see iwconfig",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Key", "key",
                 "interface/wifi", "Wireless key - see iwconfig key",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Key1", "key1",
                 "interface/wifi", "Wireless key1 - see iwconfig key[1]",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Key2", "key2",
                 "interface/wifi", "Wireless key2 - see iwconfig key[2]",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Key3", "key3",
                 "interface/wifi", "Wireless key3 - see iwconfig key[3]",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Key4", "key4",
                 "interface/wifi", "Wireless key4 - see iwconfig key[4]",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "SecurityMode", "securitymode",
                 "interface/wifi", "Wireless securitymode - see iwconfig enc",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Iwconfig", "iwconfig",
                 "interface/wifi", "Wireless iwconfig - see ifup-wireless",
                 set_roles=tech_roles)
define_accessors(current_module, Interface, "Iwpriv", "iwpriv",
                 "interface/wifi", "Wireless iwpriv - see ifup-wireless",
                 set_roles=tech_roles)

# Thierry Parmentelat - INRIA
# $Id: Accessors_standard.py 10295 2008-08-19 21:49:06Z thierry $

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

#### Wireless

define_accessors(current_module, Interface, "WifiMode", "mode", "interface/wifi", "Wifi operation mode - see iwconfig",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Essid", "essid", "interface/wifi", "Wireless essid - see iwconfig",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Nw", "nw", "interface/wifi", "Wireless nw - see iwconfig",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Freq", "freq", "interface/wifi", "Wireless freq - see iwconfig",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Channel", "channel", "interface/wifi", "Wireless channel - see iwconfig",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Sens", "sens", "interface/wifi", "Wireless sens - see iwconfig",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Rate", "rate", "interface/wifi", "Wireless rate - see iwconfig",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Key", "key", "interface/wifi", "Wireless key - see iwconfig key",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Key1", "key1", "interface/wifi", "Wireless key1 - see iwconfig key[1]",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Key2", "key2", "interface/wifi", "Wireless key2 - see iwconfig key[2]",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Key3", "key3", "interface/wifi", "Wireless key3 - see iwconfig key[3]",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Key4", "key4", "interface/wifi", "Wireless key4 - see iwconfig key[4]",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "SecurityMode", "securitymode", "interface/wifi", "Wireless securitymode - see iwconfig enc",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Iwconfig", "iwconfig", "interface/wifi", "Wireless iwconfig - see ifup-wireless",
                 get_roles=all_roles, set_roles=tech_roles)
define_accessors(current_module, Interface, "Iwpriv", "iwpriv", "interface/wifi", "Wireless iwpriv - see ifup-wireless",
                 get_roles=all_roles, set_roles=tech_roles)


# Thierry Parmentelat - INRIA
#

methods=[]

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice

from PLC.Accessors.Factory import define_accessors, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

#### example 1 : attach vlan ids on interfaces
# The third argument expose_in_api is a boolean flag that tells whether this tag may be handled
#   through the Add/Get/Update methods as a native field
#
#define_accessors(current_module, Interface, "Vlan", "vlan",
#                  "interface/general", "tag for setting VLAN id",
#                  get_roles=all_roles, set_roles=tech_roles)

##### example 2 :
# the slice page uses the category field in the following way
# it considers all tag types for which 'category' matches 'node*/ui*'
# for these, the category field is split into pieces using /
# the parts may define the following settings:
# header: to use instead of the full tagname (in which case a footnote appears with the 'description')
# type: exported as the type for the javascript table (used for how-to-sort)
# rank: to be used for sorting columns (defaults to tagname)

#################### MySlice tags
define_accessors(current_module, Node, "Reliability", "reliability",
                 # category
                 "node/monitor/ui/header=R/type=int/rank=ad",
                 # description : used to add a footnote to the table if header is set in category
                 "average reliability (% uptime) over the last week",
                  set_roles=tech_roles, expose_in_api=True)

define_accessors(current_module, Node, "Load", "load",
                 "node/monitor/ui/header=l/type=sortAlphaNumericBottom",
                 "average load (% CPU utilization) over the last week",
                  set_roles=tech_roles, expose_in_api=True)

define_accessors(current_module, Node, "ASNumber", "asnumber",
                 "node/location/ui/header=AS/type=sortAlphaNumericBottom/rank=z",
                 "Autonomous System id",
                 set_roles=tech_roles, expose_in_api=True)

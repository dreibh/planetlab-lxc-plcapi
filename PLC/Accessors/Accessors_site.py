#
# Thierry Parmentelat - INRIA
#
# Accessors_site.py is the place where you can define your own local tag accessors
# this will not be overwritten through rpm upgrades
#
# to ensure creation of new tag_types, just run 
#   service plc start accessors
# also for the running service to take the new accessors into account, you need to
#   apachectl restart
# or to stay on the safe side, simply do
#   service plc restart
#
# please note however that if a tag_type already exists in the DB, then 
# changing the corresponding accessors creation code WILL NOT alter the 
# tag_type in the DB; that applies to roles and other desc. or categ. 
# you will thus need to apply them manually 
#
# Now that Sites are taggable too, the name may be confusing, think of is as
# Accessors_local.py
#
# methods denotes the set of methods (names) that get inserted into the API
# it is updated by define_accessors

methods=[]

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Sites import Site
from PLC.Persons import Person
#from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles, person_roles, tech_roles

import sys
current_module = sys.modules[__name__]

#### example : attach vlan ids on interfaces
# The third argument expose_in_api is a boolean flag that tells whether this tag may be handled
#   through the Add/Get/Update methods as a native field
#
#define_accessors(current_module, Interface, "Vlan", "vlan",
#                  "interface/general", "tag for setting VLAN id",
#                  get_roles=all_roles, set_roles=tech_roles)

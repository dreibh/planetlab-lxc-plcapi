#
# Thierry Parmentelat - INRIA
#
# Accessors_site.py is the place where you can define your own local tag accessors
# this will not be overwritten through rpm upgrades
#
# Historical note: now that Sites are taggable too, the name may be confusing, 
# think of this as Accessors_local.py
#
# to ensure creation of new tag_types, just run 
#   service plc start accessors
# also for the running API to take the new accessors into account, you need to
#   apachectl restart
# or to stay on the safe side, simply do
#   service plc restart
#
# methods denotes the set of methods (names) that get inserted into the API
# it is updated by define_accessors

methods=[]

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Sites import Site
from PLC.Persons import Person

from PLC.Accessors.Factory import define_accessors, all_roles, person_roles, tech_roles

import sys
current_module = sys.modules[__name__]

#### example : attach vlan ids on interfaces
#
#define_accessors(current_module, Interface, "Vlan", "vlan",
#                  "interface/general", "tag for setting VLAN id",
#                  get_roles=all_roles, set_roles=tech_roles)
#
# The optional expose_in_api is a boolean flag that tells whether this tag may be handled
#   through the Add/Get/Update methods as a native field
# e.g. 
#define_accessors(current_module, Node, "Foo", "foo",
#                  "node/example", "my own description for foo",
#                  get_roles=all_roles, set_roles=all_roles)
# will let you do
# GetNodes ( {'foo':'*bar*'},['hostname','foo'])
#
# 

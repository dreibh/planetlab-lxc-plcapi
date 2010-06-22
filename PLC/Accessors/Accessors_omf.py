# Thierry Parmentelat - INRIA
# $Id$
# $URL$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Slices import Slice
from PLC.Sites import Site
from PLC.Persons import Person

from PLC.Accessors.Factory import define_accessors, admin_roles, all_roles, tech_roles

import sys
current_module = sys.modules[__name__]

define_accessors(current_module, Slice, "OmfControl","omf_control",
                 "slice/usertools","Pre-install and configure OMF Resource Controller in slice if set",
                 get_roles=all_roles, set_roles=all_roles, expose_in_api=True)

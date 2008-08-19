# Thierry Parmentelat - INRIA
# $Id$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Accessors.Factory import define_accessors, all_roles

import sys
current_module = sys.modules[__name__]

# example : node architecture 
define_accessors(current_module, Node, "Arch", 'arch',  'node/config', 'architecture name', 
                 tag_min_role_id=40,
                 get_roles=all_roles,
                 set_roles=['admin', 'pi', 'tech'] )


# Thierry Parmentelat - INRIA
# $Id$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Shortcuts.Factory import all_roles, get_set_factory

methods=[]

# example : node architecture 
(GetNodeArch, SetNodeArch) = \
    get_set_factory ( Node, "Arch", 'arch',  'node/config', 'architecture name', 
                      tag_min_role_id=40, 
                      get_roles=all_roles,
                      set_roles=['admin', 'pi', 'tech'] )
methods += [ 'GetNodeArch', 'SetNodeArch' ]


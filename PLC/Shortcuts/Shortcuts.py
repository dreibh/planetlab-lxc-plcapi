# Thierry Parmentelat - INRIA
# $Id$

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.Shortcuts.Factory import get_set_factory

# xxx probably defined someplace else
all_roles = [ 'admin', 'pi', 'tech', 'user', 'node' ]

methods=[]

# example : node architecture 
(GetNodeArch, SetNodeArch) = \
    get_set_factory ( Node, "Arch", 'arch',  'node/config', 'architecture name', 
                      tag_min_role_id=40, 
                      get_roles=all_roles,
                      set_roles=['admin', 'pi', 'tech'] )
methods += [ 'GetNodeArch', 'SetNodeArch' ]

# example : vlan ids on interfaces
(GetInterfaceVlan, SetInterfaceVlan) = \
    get_set_factory ( Interface, "Vlan", "vlan","interface/general", "tag for setting VLAN id",
                      get_roles=all_roles,
                      set_roles=['admin', 'pi', 'tech'] )
methods += [ 'GetInterfaceVlan', 'SetInterfaceVlan' ]

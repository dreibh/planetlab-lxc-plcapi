# Thierry Parmentelat - INRIA
# $Id$

from PLC.Method import Method
import v42legacy
import sys
current_module=sys.modules[__name__]

methods = [
    "AddNodeNetwork",
    "AddNodeNetworkSetting",
    "DeleteNodeNetwork",
    "DeleteNodeNetworkSetting",
    "GetNodeNetworkSettings",
    "GetNodeNetworks",
    "UpdateNodeNetwork",
    "UpdateNodeNetworkSetting",
]

# argument mapping
v42_to_v43_argmap = {
    "nodenetwork_id":"interface_id",
    "nodenetwork_ids":"interface_ids",
    "nodenetworksetting_ids":"interface_tag_ids",
    }
v43_to_v42_argmap = dict([ (v,k) for k,v in v42_to_v43_argmap.iteritems()])
def v42rename (x): return v42_to_v43_argmap.get(x,x)
def v43rename (x): return v43_to_v42_argmap.get(x,x)

# attach methods here
for legacyname in methods:
    # new method name
    newname=legacyname.replace("NodeNetwork","Interface").replace("Setting","Tag")
    path = "PLC.Methods."
    setattr(current_module,legacyname,v42legacy.make_class(legacyname,newname,path,v42rename,v43rename))


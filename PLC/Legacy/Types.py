# Thierry Parmentelat - INRIA
# $Id$

from PLC.Method import Method
import v42legacy
import sys
current_module=sys.modules[__name__]

def import_deep(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

v42_to_v43_methodmap = {
    "AddSliceAttributeType"         : "AddTagType",
    "DeleteSliceAttributeType"      : "DeleteTagType",
    "GetSliceAttributeTypes"        : "GetTagTypes",
    "UpdateSliceAttributeType"      : "UpdateTagType",
    "AddNodeNetworkSettingType"     : "AddTagType",
    "DeleteNodeNetworkSettingType"  : "DeleteTagType",
    "GetNodeNetworkSettingTypes"    : "GetTagTypes",
    "UpdateNodeNetworkSettingType"  : "UpdateTagType",
}    

methods = v42_to_v43_methodmap.keys()

v42_to_v43_argmap = { "name":"tagname" }
v43_to_v42_argmap = dict([ (v,k) for k,v in v42_to_v43_argmap.iteritems()])

def v42rename (x): return v42_to_v43_argmap.get(x,x)
def v43rename (x): return v43_to_v42_argmap.get(x,x)

# attach methods here
for legacyname in methods:
    # new method name
    newname=v42_to_v43_methodmap[legacyname]
    path = "PLC.Methods."
    setattr(current_module,legacyname,v42legacy.make_class(legacyname,newname,path,import_deep,v42rename,v43rename))

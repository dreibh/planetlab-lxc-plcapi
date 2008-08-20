# Thierry Parmentelat - INRIA
# $Id$

from PLC.Method import Method

def import_deep(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

map = {
    "AddSliceAttributeType"         : "AddTagType",
    "DeleteSliceAttributeType"      : "DeleteTagType",
    "GetSliceAttributeTypes"        : "GetTagTypes",
    "UpdateSliceAttributeType"      : "UpdateTagType",
    "AddNodeNetworkSettingType"     : "AddTagType",
    "DeleteNodeNetworkSettingType"  : "DeleteTagType",
    "GetNodeNetworkSettingTypes"    : "GetTagTypes",
    "UpdateNodeNetworkSettingType"  : "UpdateTagType",
}    

methods = map.keys()

# does any required renaming
def rename (x):
    if x=='name':
        return 'tagname'
    else:
        return x

# apply rename on list (columns) or dict (filter) args
def patch_legacy_arg (arg):
    if isinstance(arg,list):
        return [rename(x) for x in arg]
    if isinstance(arg,dict):
        return dict ( [ (rename(k),v) for (k,v) in arg.iteritems() ] )
    return arg

def legacy_method (legacyname, newname):
    # locate new class
    newclass=getattr(import_deep("PLC.Methods."+newname),newname)
    # create class for legacy name
    legacyclass = type(legacyname,(newclass,), 
                       {"__doc__":"Legacy method - please use %s instead"%newname})
    for internal in ["roles","accepts","returns"]:
        setattr(legacyclass,internal,getattr(newclass,internal))
    # turn off type checking, as introspection code fails on wrapped_call
    setattr(legacyclass,"skip_typecheck",True)
    # rewrite call
    def wrapped_call (self,auth,*args, **kwds):
        newargs=[patch_legacy_arg(x) for x in args]
        newkwds=dict ( [ (k,patch_legacy_arg(v)) for (k,v) in kwds.iteritems() ] )
        return getattr(newclass,"call")(self,auth,*newargs,**newkwds)
    setattr(legacyclass,"call",wrapped_call)

    return legacyclass

import sys
current_module=sys.modules[__name__]

for (legacyname,newname) in map.iteritems():
    setattr(current_module,legacyname,legacy_method(legacyname,newname))


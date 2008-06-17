# Thierry Parmentelat - INRIA
# $Id$

from PLC.Method import Method

def import_deep(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

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

# does any required renaming
def rename (x):
    if x=='nodenetwork_id':
        return 'interface_id'
    if x=='nodenetwork_ids':
        return 'interface_ids'
    else:
        return x

# apply rename on list (columns) or dict (filter) args
def patch_legacy_arg (arg):
    if isinstance(arg,list):
        return [rename(x) for x in arg]
    if isinstance(arg,dict):
        return dict ( [ (rename(k),v) for (k,v) in arg.iteritems() ] )
    return arg

def factory (legacyname):
    # new method name
    newname=legacyname.replace("NodeNetwork","Interface")
    # locate new class
    newclass=getattr(import_deep("PLC.Methods."+newname),newname)
    # create class for legacy name
    legacyclass = type(legacyname,(newclass,), 
                       {"__doc__":"Legacy method - please use %s instead"%newname})
    # xxx should rewrite 'call' to handle any argument using nodenetwork_id(s)
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

# this does not work, as __module__ is not yet supported
#for legacyname in methods:
#   setattr(__module__,legacyname,factory(legacyname))
# this does not work either, as we are importing the module so we cannot locate it yet
#for legacyname in methods:
#    this_module = import_deep(__name__)
#    setattr(__module__,legacyname,factory(legacyname))

AddNodeNetwork=factory("AddNodeNetwork")
AddNodeNetworkSetting=factory("AddNodeNetworkSetting")
DeleteNodeNetwork=factory("DeleteNodeNetwork")
DeleteNodeNetworkSetting=factory("DeleteNodeNetworkSetting")
GetNodeNetworkSettings=factory("GetNodeNetworkSettings")
GetNodeNetworks=factory("GetNodeNetworks")
UpdateNodeNetwork=factory("UpdateNodeNetwork")
UpdateNodeNetworkSetting=factory("UpdateNodeNetworkSetting")

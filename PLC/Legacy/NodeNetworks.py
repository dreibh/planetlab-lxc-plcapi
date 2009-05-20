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
v42_to_v43_renaming = {
    "nodenetwork_id":"interface_id",
    "nodenetwork_ids":"interface_ids",
    "nodenetworksetting_ids":"interface_tag_ids",
    }

v43_to_v42_renaming = dict([ (v,k) for k,v in v42_to_v43_renaming.iteritems()])

for k,v in v42_to_v43_renaming.iteritems():
    v43_to_v42_renaming[v]=k

def v42rename (x):
    return v42_to_v43_renaming.get(x,x)

def v43rename (x):
    return v43_to_v42_renaming.get(x,x)


# apply rename on list (columns) or dict (filter) args
def patch_legacy (arg,rename):
    if isinstance(arg,list):
        for i in range(0,len(arg)):
            arg[i] = patch_legacy(arg[i],rename)
        return arg
    if isinstance(arg,dict):
        return dict ( [ (rename(k),v) for (k,v) in arg.iteritems() ] )
    return rename(arg)

def legacy_method (legacyname):
    # new method name
    newname=legacyname.replace("NodeNetwork","Interface").replace("Setting","Tag")
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
	print "%s: self.caller = %s, self=%s" % (legacyname,self.caller,self)
        newargs=[patch_legacy(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch_legacy(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = getattr(newclass,"call")(self,auth,*newargs,**newkwds)
        return patch_legacy(results,v43rename)
    setattr(legacyclass,"call",wrapped_call)

    return legacyclass

import sys
current_module=sys.modules[__name__]

# attach
for legacyname in methods:
    setattr(current_module,legacyname,legacy_method(legacyname))


# $Id: $

def import_deep(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

# apply rename on list (columns) or dict (filter) args
def patch (arg,rename):
    if isinstance(arg,list):
        for i in range(0,len(arg)):
            arg[i] = patch(arg[i],rename)
        return arg
    if isinstance(arg,dict):
        return dict ( [ (rename(k),v) for (k,v) in arg.iteritems() ] )
    return rename(arg)


def make_class (legacyname,newname,path,v42rename,v43rename):
    # locate new class
    newclass=getattr(import_deep(path+newname),newname)
    # create class for legacy name
    legacyclass = type(legacyname,(newclass,), 
                       {"__doc__":"Legacy method - please use %s instead"%newname})
    for internal in ["roles","accepts","returns"]:
        setattr(legacyclass,internal,getattr(newclass,internal))
    # turn off type checking, as introspection code fails on wrapped_call
    setattr(legacyclass,"skip_typecheck",True)
    # rewrite call
    def wrapped_call (self,auth,*args, **kwds):
	# print "%s: self.caller = %s, self=%s" % (legacyname,self.caller,self)
        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = getattr(newclass,"call")(self,auth,*newargs,**newkwds)
        return patch(results,v43rename)
    setattr(legacyclass,"call",wrapped_call)

    return legacyclass


# $Id: $

from PLC.Method import Method
from PLC.Auth import Auth
import PLC.Auth

# apply rename on list (columns) or dict (filter) args
def patch (arg,rename):
    if isinstance(arg,list):
        for i in range(0,len(arg)):
            arg[i] = patch(arg[i],rename)
        return arg
    if isinstance(arg,dict):
        return dict ( [ (rename(k),v) for (k,v) in arg.iteritems() ] )
    return rename(arg)

def make_class (legacyname,newname,path,import_deep,v42rename,v43rename):
    # locate new class
    newclass=getattr(import_deep(path+newname),newname)
    setattr(newclass,"__origcall",getattr(newclass,"call"))
    # create class for legacy name
    legacyclass = type(legacyname,(newclass,), 
                       {"__doc__":"Legacy method - please use %s instead"%newname})
    for internal in ["roles","accepts","returns"]:
        setattr(legacyclass,internal,getattr(newclass,internal))
    # turn off type checking, as introspection code fails on wrapped_call
    setattr(legacyclass,"skip_typecheck",True)
    # rewrite call
    def wrapped_call (self,auth,*args, **kwds):
	#print "%s: self.caller = %s, auth=%s, self.api=%s, self=%s" % (legacyname,self.caller,auth,self.api,self)
        if not hasattr(self,"auth"):
            self.auth = None

        if self.auth == None and auth <> None:
            self.auth = auth

        if self.auth <> None and self.caller == None:
            a = PLC.Auth.map_auth(auth)
            print "a = %s" % a
            a.check(self,auth,*args)

        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = self.__origcall(auth,*newargs,**newkwds)
        return patch(results,v43rename)
    setattr(legacyclass,"call",wrapped_call)

    return legacyclass


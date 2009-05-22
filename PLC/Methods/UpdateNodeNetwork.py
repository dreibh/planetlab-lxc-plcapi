
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworks import v42rename, v43rename
from PLC.Methods.UpdateInterface import UpdateInterface
class UpdateNodeNetwork(UpdateInterface):
    """ Legacy version of UpdateInterface. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, *args, **kwds):
        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = UpdateInterface.call(self,auth,*newargs,**newkwds)
        return patch(results,v43rename)


from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworkSettings import v42rename, v43rename
from PLC.Methods.DeleteInterfaceTag import DeleteInterfaceTag
class DeleteNodeNetworkSetting(DeleteInterfaceTag):
    """ Legacy version of DeleteInterfaceTag. """
    skip_typecheck = True
    def call(self, auth, *args, **kwds):
        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = DeleteInterfaceTag.call(self,auth,*newargs,**newkwds)
        return patch(results,v43rename)

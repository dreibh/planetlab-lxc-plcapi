
from PLC.v42Legacy import patch
from PLC.v42LegacyTypes import v42rename, v43rename
from PLC.Methods.DeleteTagType import DeleteTagType
class DeleteNodeNetworkSettingType(DeleteTagType):
    """ Legacy version of DeleteTagType. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, *args, **kwds):
        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = DeleteTagType.call(self,auth,*newargs,**newkwds)
        return patch(results,v43rename)

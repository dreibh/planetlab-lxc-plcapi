
from PLC.v42Legacy import patch
from PLC.v42LegacySliceAttributes import v42rename, v43rename
from PLC.Methods.DeleteSliceTag import DeleteSliceTag
class DeleteSliceAttribute(DeleteSliceTag):
    """ Legacy version of DeleteSliceTag. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, *args, **kwds):
        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = DeleteSliceTag.call(self,auth,*newargs,**newkwds)
        return patch(results,v43rename)

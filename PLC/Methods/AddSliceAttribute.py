
from PLC.v42Legacy import patch
from PLC.v42LegacySliceAttributes import v42rename, v43rename
from PLC.Methods.AddSliceTag import AddSliceTag
class AddSliceAttribute(AddSliceTag):
    """ Legacy version of AddSliceTag. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, *args, **kwds):
        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = AddSliceTag.call(self,auth,*newargs,**newkwds)
        return patch(results,v43rename)

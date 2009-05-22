
from PLC.v42Legacy import patch
from PLC.v42LegacyAttributeTypes import v42rename, v43rename
from PLC.Methods.UpdateTagType import UpdateTagType
class UpdateSliceAttributeType(UpdateTagType):
    """ Legacy version of UpdateTagType. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, *args, **kwds):
        newargs=[patch(x,v42rename) for x in args]
        newkwds=dict ( [ (k,patch(v,v42rename)) for (k,v) in kwds.iteritems() ] )
        results = UpdateTagType.call(self,auth,*newargs,**newkwds)
        return patch(results,v43rename)

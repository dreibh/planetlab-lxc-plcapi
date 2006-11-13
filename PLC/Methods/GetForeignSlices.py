#
# Thierry Parmentelat - INRIA
# 

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.ForeignSlices import ForeignSlice, ForeignSlices

class GetForeignSlices(Method):
    """
    Returns an array of structs containing details about foreign
    slices. If foreign_slice_filter is specified and is an array of
    foreign slice identifiers or names, or a struct of foreign slice
    attributes, only foreign slices matching the filter will be
    returned. If return_fields is specified, only the specified
    details will be returned.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed([Mixed(ForeignSlice.fields['slice_id'],
                     ForeignSlice.fields['name'])],
              Filter(ForeignSlice.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]
    
    returns = [ForeignSlice.fields]

    def call(self, auth, foreign_slice_filter = None, return_fields = None):
	return ForeignSlices(self.api, foreign_slice_filter, return_fields)

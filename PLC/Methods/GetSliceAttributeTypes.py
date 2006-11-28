from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes

class GetSliceAttributeTypes(Method):
    """
    Returns an array of structs containing details about slice
    attribute types. If attribute_type_filter is specified and
    is an array of slice attribute type identifiers, or a
    struct of slice attribute type attributes, only slice attribute
    types matching the filter will be returned. If return_fields is
    specified, only the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed([Mixed(SliceAttributeType.fields['attribute_type_id'],
                     SliceAttributeType.fields['name'])],
              Filter(SliceAttributeType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [SliceAttributeType.fields]

    event_type = 'Get'
    object_type = 'SliceAttributeType'

    def call(self, auth, attribute_type_filter = None, return_fields = None):
        return SliceAttributeTypes(self.api, attribute_type_filter, return_fields)

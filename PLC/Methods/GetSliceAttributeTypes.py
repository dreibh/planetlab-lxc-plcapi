from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes

class GetSliceAttributeTypes(Method):
    """
    Return an array of structs containing details about all possible
    slice and node attributes. If attribute_id_or_name_list is
    specified, only the specified attributes will be queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed([Mixed(SliceAttributeType.fields['attribute_type_id'],
                     SliceAttributeType.fields['name'])],
              Filter(SliceAttributeType.fields))
        ]

    returns = [SliceAttributeType.fields]

    def call(self, auth, attribute_type_filter = None):
        return SliceAttributeTypes(self.api, attribute_type_filter).values()

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes
from PLC.Auth import Auth

class DeleteSliceAttributeType(Method):
    """
    Deletes the specified slice attribute.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(SliceAttributeType.fields['attribute_type_id'],
              SliceAttributeType.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, attribute_type_id_or_name):
        attribute_types = SliceAttributeTypes(self.api, [attribute_type_id_or_name])
        if not attribute_types:
            raise PLCInvalidArgument, "No such slice attribute type"
        attribute_type = attribute_types[0]
	PLCCheckLocalSliceAttributeType(attribute_type,"DeleteSliceAttributeType")

        attribute_type.delete()
	self.object_ids = [attribute_type['attribute_type_id']]

        return 1

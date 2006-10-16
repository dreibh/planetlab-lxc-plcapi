from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes
from PLC.Auth import PasswordAuth

class DeleteSliceAttributeType(Method):
    """
    Deletes the specified slice attribute.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        Mixed(SliceAttributeType.fields['attribute_type_id'],
              SliceAttributeType.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, attribute_type_id_or_name):
        attribute_types = SliceAttributeTypes(self.api, [attribute_type_id_or_name]).values()
        if not attribute_types:
            raise PLCInvalidArgument, "No such slice attribute type"
        attribute_type = attribute_types[0]

        attribute_type.delete()

        return 1

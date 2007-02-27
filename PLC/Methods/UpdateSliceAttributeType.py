from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['name', 'description', 'min_role_id']

class UpdateSliceAttributeType(Method):
    """
    Updates the parameters of an existing attribute with the values in
    attribute_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    attribute_type_fields = dict(filter(can_update, SliceAttributeType.fields.items()))

    accepts = [
        Auth(),
        Mixed(SliceAttributeType.fields['attribute_type_id'],
              SliceAttributeType.fields['name']),
        attribute_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, attribute_type_id_or_name, attribute_type_fields):
        attribute_type_fields = dict(filter(can_update, attribute_type_fields.items()))

        attribute_types = SliceAttributeTypes(self.api, [attribute_type_id_or_name])
        if not attribute_types:
            raise PLCInvalidArgument, "No such attribute"
        attribute_type = attribute_types[0]

        attribute_type.update(attribute_type_fields)
        attribute_type.sync()
	self.event_objects = {'AttributeType': [attribute_type['attribute_type_id']]}

        return 1

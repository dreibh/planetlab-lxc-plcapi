from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['description', 'min_role_id']

class AddSliceAttributeType(Method):
    """
    Adds a new type of slice attribute. Any fields specified in
    attribute_type_fields are used, otherwise defaults are used.

    Returns the new attribute_type_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin']

    update_fields = dict(filter(can_update, SliceAttributeType.fields.items()))

    accepts = [
        PasswordAuth(),
        SliceAttributeType.fields['name'],
        update_fields
        ]

    returns = Parameter(int, 'New attribute_id (> 0) if successful')

    def call(self, auth, name, attribute_type_fields = {}):
        attribute_type_fields = dict(filter(can_update, attribute_type_fields.items()))
        attribute_type = SliceAttributeType(self.api, attribute_type_fields)
        attribute_type['name'] = name
        attribute_type.sync()

        return attribute_type['attribute_type_id']
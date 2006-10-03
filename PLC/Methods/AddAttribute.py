from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Attributes import Attribute, Attributes
from PLC.Auth import PasswordAuth

class AddAttribute(Method):
    """
    Adds a new type of attribute. Any fields specified in optional_vals
    are used, otherwise defaults are used.

    Returns the new attribute_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    can_update = lambda (field, value): field in \
                 ['description', 'min_role_id']
    update_fields = dict(filter(can_update, Attribute.fields.items()))

    accepts = [
        PasswordAuth(),
        Attribute.fields['name'],
        update_fields
        ]

    returns = Parameter(int, 'New attribute_id (> 0) if successful')

    def call(self, auth, name, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid field specified"

        attribute = Attribute(self.api, optional_vals)
        attribute['name'] = name
        attribute.sync()

        return attribute['attribute_id']

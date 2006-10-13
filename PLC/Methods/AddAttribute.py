from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Attributes import Attribute, Attributes
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['description', 'min_role_id']

class AddAttribute(Method):
    """
    Adds a new type of attribute. Any fields specified in
    attribute_fields are used, otherwise defaults are used.

    Returns the new attribute_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    update_fields = dict(filter(can_update, Attribute.fields.items()))

    accepts = [
        PasswordAuth(),
        Attribute.fields['name'],
        update_fields
        ]

    returns = Parameter(int, 'New attribute_id (> 0) if successful')

    def call(self, auth, name, attribute_fields = {}):
        attribute_fields = dict(filter(can_update, attribute_fields.items()))
        attribute = Attribute(self.api, attribute_fields)
        attribute['name'] = name
        attribute.sync()

        return attribute['attribute_id']

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Attributes import Attribute, Attributes
from PLC.Auth import PasswordAuth

class UpdateAttribute(Method):
    """
    Updates the parameters of an existing attribute with the values in
    update_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    can_update = lambda (field, value): field in \
                 ['description', 'min_role_id']
    update_fields = dict(filter(can_update, Attribute.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Attribute.fields['attribute_id'],
              Attribute.fields['name']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, attribute_id_or_name, update_fields):
        if filter(lambda field: field not in self.update_fields, update_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        attributes = Attributes(self.api, [attribute_id_or_name]).values()
        if not attributes:
            raise PLCInvalidArgument, "No such attribute"
        attribute = attributes[0]

        attribute.update(update_fields)

        attribute.sync()

        return 1

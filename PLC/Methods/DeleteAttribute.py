from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Attributes import Attribute, Attributes
from PLC.Auth import PasswordAuth

class DeleteAttribute(Method):
    """
    Deletes the specified slice attribute.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        Mixed(Attribute.fields['attribute_id'],
              Attribute.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, attribute_id_or_name):
        attributes = Attributes(self.api, [attribute_id_or_name]).values()
        if not attributes:
            raise PLCInvalidArgument, "No such attribute"
        attribute = attributes[0]

        attribute.delete()

        return 1

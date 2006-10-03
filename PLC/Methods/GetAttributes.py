from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Attributes import Attribute, Attributes

class GetAttributes(Method):
    """
    Return an array of structs containing details about all possible
    slice and node attributes. If attribute_id_or_name_list is
    specified, only the specified attributes will be queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Attribute.fields['attribute_id'],
               Attribute.fields['name'])],
        ]

    returns = [Attribute.fields]

    def call(self, auth, attribute_id_or_name_list = None):
        # Get slice attribute information
        attributes = Attributes(self.api, attribute_id_or_name_list).values()

        return attributes

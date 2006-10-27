from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Addresses import Address, Addresses
from PLC.Auth import Auth

class GetAddresses(Method):
    """
    Get an array of structs containing details about addresses. If
    address_id_list is specified, only the specified addresses will be
    queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        [Address.fields['address_id']],
        ]

    returns = [Address.fields]

    def call(self, auth, address_id_list = None):
        return Addresses(self.api, address_id_list).values()

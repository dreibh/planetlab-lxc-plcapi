from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import Auth
from PLC.Methods.AddAddressType import AddAddressType

class AdmAddAddressType(AddAddressType):
    """
    Deprecated. See AddAddressType.
    """

    status = "deprecated"

    accepts = [
        Auth(),
        AddressType.fields['name']
        ]

    def call(self, auth, name):
        return AddAddressType.call(self, auth, {'name': name})

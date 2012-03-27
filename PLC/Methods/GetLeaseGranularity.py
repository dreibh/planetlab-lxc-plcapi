from PLC.Method import Method
from PLC.Auth import Auth
from PLC.Faults import *
from PLC.Parameter import Parameter

class GetLeaseGranularity(Method):
    """
    Returns the granularity in seconds for the reservation system
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node', 'anonymous']

    accepts = [
        Auth(),
        ]

    # for now only return /etc/myplc-release verbatim
    returns = Parameter (int, "the granularity in seconds for the reservation system")

    def call(self, auth):

        return self.api.config.PLC_RESERVATION_GRANULARITY

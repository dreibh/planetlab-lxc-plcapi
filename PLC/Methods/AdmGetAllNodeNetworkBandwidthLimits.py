import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import PasswordAuth

class AdmGetAllNodeNetworkBandwidthLimits(Method):
    """
    Returns an array of all the valid bandwith limits for node networks.

    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth()
        ]

    returns = [NodeNetwork.fields['bwlimit']]

    def call(self, auth):
        # Authenticated function
        assert self.caller is not None

        nodenetwork_bwlimits = NodeNetwork.bwlimits          

        return nodenetwork_bwlimits

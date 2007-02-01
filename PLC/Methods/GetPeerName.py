from PLC.Method import Method
from PLC.Parameter import Parameter
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers

class GetPeerName (Method):
    """
    Returns this peer's name, as defined in the config as PLC_NAME
    """

    roles = ['admin', 'peer', 'node']

    accepts = [Auth()]

    returns = Peer.fields['peername']

    def call (self, auth):
        return self.api.config.PLC_NAME

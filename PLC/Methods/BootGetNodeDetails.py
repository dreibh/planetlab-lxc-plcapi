from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import BootAuth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Sessions import Session, Sessions

class BootGetNodeDetails(Method):
    """
    Returns a set of details about the calling node, including a new
    node session value.
    """

    accepts = [BootAuth()]
    returns = {
        'hostname': Node.fields['hostname'],
        'boot_state': Node.fields['boot_state'],
        'model': Node.fields['model'],
        'networks': [NodeNetwork.fields],
        'session': Session.fields['session_id'],
        }

    def call(self, auth, update_fields):
        details = {
            'hostname': self.caller['hostname'],
            'boot_state': self.caller['boot_state'],
            'model': self.caller['model'],
            }

        # Generate a new session value
        session = Session(self.api)
        session.sync(commit = False)
        session.add_node(self.caller, commit = True)

        details['session'] = session['session_id']

        if self.caller['nodenetwork_ids']:
            details['networks'] = NodeNetworks(self.api, self.caller['nodenetwork_ids']).values()

        return details

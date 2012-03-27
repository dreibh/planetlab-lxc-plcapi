from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import BootAuth
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.Sessions import Session, Sessions

class BootGetNodeDetails(Method):
    """
    Returns a set of details about the calling node, including a new
    node session value.
    """

    roles = ['node']

    accepts = [BootAuth()]

    returns = {
        'hostname': Node.fields['hostname'],
        'boot_state': Node.fields['boot_state'],
        'model': Node.fields['model'],
        'networks': [Interface.fields],
        'session': Session.fields['session_id'],
        }

    def call(self, auth):
        details = {
            'hostname': self.caller['hostname'],
            'boot_state': self.caller['boot_state'],
            # XXX Boot Manager cannot unmarshal None
            'model': self.caller['model'] or "",
            }

        # Generate a new session value
        session = Session(self.api)
        session.sync(commit = False)
        session.add_node(self.caller, commit = True)

        details['session'] = session['session_id']

        if self.caller['interface_ids']:
            details['networks'] = Interfaces(self.api, self.caller['interface_ids'])
            # XXX Boot Manager cannot unmarshal None
            for network in details['networks']:
                for field in network:
                    if network[field] is None:
                        if isinstance(network[field], (int, long)):
                            network[field] = -1
                        else:
                            network[field] = ""

        self.message = "Node request boot_state (%s) and networks" % \
                (details['boot_state'])
        return details

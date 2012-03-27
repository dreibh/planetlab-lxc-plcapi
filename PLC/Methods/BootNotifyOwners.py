from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth, BootAuth, SessionAuth
from PLC.Nodes import Node, Nodes
from PLC.Messages import Message, Messages

from PLC.Boot import notify_owners

class BootNotifyOwners(Method):
    """
    Notify the owners of the node, and/or support about an event that
    happened on the machine.

    Returns 1 if successful.
    """

    roles = ['node']

    accepts = [
        Auth(),
        Message.fields['message_id'],
        Parameter(int, "Notify PIs"),
        Parameter(int, "Notify technical contacts"),
        Parameter(int, "Notify support")
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, message_id, include_pis, include_techs, include_support):
        assert isinstance(self.caller, Node)
        notify_owners(self, self.caller, message_id, include_pis, include_techs, include_support)
        return 1

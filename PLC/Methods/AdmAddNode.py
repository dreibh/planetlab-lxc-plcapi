from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth
from PLC.Methods.AddNode import AddNode

class AdmAddNode(AddNode):
    """
    Deprecated. See AddNode.
    """

    status = "deprecated"

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        Node.fields['hostname'],
        Node.fields['boot_state'],
        AddNode.update_fields
        ]

    def call(self, auth, site_id_or_login_base, hostname, boot_state, node_fields = {}):
        node_fields['boot_state'] = boot_state
        return AddNode.call(self, auth, site_id_or_login_base, hostname, node_fields)

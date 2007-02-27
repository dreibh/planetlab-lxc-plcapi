from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites
from PLC.Auth import Auth
from PLC.Methods.AddNode import AddNode

can_update = lambda (field, value): field in \
             ['model', 'version']

class AdmAddNode(AddNode):
    """
    Deprecated. See AddNode.
    """

    status = "deprecated"

    node_fields = dict(filter(can_update, Node.fields.items()))

    accepts = [
        Auth(),
        Site.fields['site_id'],
        Node.fields['hostname'],
        Node.fields['boot_state'],
        node_fields
        ]

    def call(self, auth, site_id, hostname, boot_state, node_fields = {}):
        node_fields['site_id'] = site_id
        node_fields['hostname'] = hostname
        node_fields['boot_state'] = boot_state
        return AddNode.call(self, auth, node_fields)

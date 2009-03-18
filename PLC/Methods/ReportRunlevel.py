# $Id$
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth, BootAuth, SessionAuth
from PLC.Nodes import Node, Nodes

can_update = ['run_level']

class ReportRunlevel(Method):
    """
        report runlevel
    """
    roles = ['node', 'admin']

    accepts = [
        Mixed(BootAuth(), SessionAuth(), Auth()),
        {'run_level': Node.fields['run_level'],
         },
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, report_fields, node_id_or_hostname=None):

        if not isinstance(self.caller, Node):
            # check admin
            if 'admin' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not allowed to update node run_level"

            nodes = Nodes(self.api, [node_id_or_hostname])
            if not nodes:
                raise PLCInvalidArgument, "No such node"
        else:
            nodes  = [self.caller]

        node = nodes[0]

        node.update_last_contact()
        for field in can_update:
            if field in report_fields:
                node.update({field : report_fields[field]})

        node.sync(commit=True)

        self.message = "Node Runlevel Report : %s" % ", ".join(report_fields.keys())

        return 1

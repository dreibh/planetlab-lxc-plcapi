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
        # avoid logging this even too often
        # avoid logging occurrences where run_level does not change
        former_level=None
        if 'run_level' in node: former_level=node['run_level']

        node.update_last_contact()
        for field in can_update:
            if field in report_fields:
                node.update({field : report_fields[field]})

        node.sync(commit=True)

        # skip logging in this case
        if former_level and 'run_level' in node and node['run_level'] == former_level:
            pass
        else:
            # handle the 'run_level' key
            message="run level " + node['hostname'] + ":"
            if 'run_level' in report_fields:
                message += str(former_level) + "->" + report_fields['run_level']
            message += ", ".join(  [ k + "->" + v for (k,v) in report_fields.items() if k not in ['run_level'] ] )

        return 1

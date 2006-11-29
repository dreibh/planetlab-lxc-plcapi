from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Nodes import Node, Nodes
from PLC.Auth import Auth

class AddConfFileToNode(Method):
    """
    Adds a configuration file to the specified node. If the node is
    already linked to the configuration file, no errors are returned.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        ConfFile.fields['conf_file_id'],
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, conf_file_id, node_id_or_hostname):
	# Get configuration file
        conf_files = ConfFiles(self.api, [conf_file_id])
        if not conf_files:
            raise PLCInvalidArgument, "No such configuration file"
        conf_file = conf_files[0]

        # Get node
	nodes = Nodes(self.api, [node_id_or_hostname])
	if not nodes:
		raise PLCInvalidArgument, "No such node"
	node = nodes[0]
	
	# Link configuration file to node
        if node['node_id'] not in conf_file['node_ids']:
            conf_file.add_node(node)

        # Log affected objects
        self.object_ids = [conf_file_id, node['node_id']]

        return 1

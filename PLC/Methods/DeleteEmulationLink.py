# Delete an Emulation link
#
# Marta Carbone - unipi
# $Id$

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.NodeTags import *
from PLC.Accessors.Accessors_dummynetbox import * # import dummynet accessors

class DeleteEmulationLink(Method):
    """
    Delete a connection between a node and a dummynetbox.

    Returns 1 if successful, faults otherwise.

    """
    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Parameter(int, 'node_id'),
    ]

    returns = Parameter(int, '1 is successful, 0 if not found, fault otherwise')

    def call(self, auth, node_id):

        assert self.caller is not None

	# check for node existence
        nodes= Nodes(self.api, [node_id])
        if not nodes:
            raise PLCInvalidArgument, "Node %s not found" % node_id

        # check for roles permission to call this method
        if 'admin' not in self.caller['roles']:
            if site not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete this link"

        # check for the right subclass
	subclass = GetNodeSubclass(self.api)
	node_subclass = subclass.call(auth, node_id)
	if node_subclass != None:
		raise  PLCInvalidArgument, "%s is not a node, subclass is %s" % (node_id, node_subclass)

        # Delete from the nodetags the entry with
	# the given node_id and tagtype = 'dummynetbox'
        nodetag = NodeTags(self.api, {'node_id':node_id, 'tagname':'dummynetbox_id'})

	if not nodetag:
	    return 0

	nodetag[0].delete()

        return 1

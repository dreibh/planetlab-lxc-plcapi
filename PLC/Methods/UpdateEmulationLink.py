# Connect a Node with a Dummynet box, using Accessors
#
# Marta Carbone - unipi
# $Id$
# $URL$

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Sites import Site, Sites
from PLC.Auth import Auth
from PLC.Accessors.Accessors_dummynetbox import *			# import dummynet accessors

class UpdateEmulationLink(Method):
    """
    Connect a Node with a Dummynet box.
    Takes as input two node_id, the first should be a regular node,
    the second a dummynet box.

    This operation is restricted to PIs and techs owner of the site
    on which the Dummynet box and the Node are located.
    Admins may create emulation links for any site, but the Dummynet
    and the Node must belong to the same site.

    XXX Dummynet accessors should not be called directly, since they can
    be used to create connection whitout checks.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Parameter(int, 'node_id'),	 # a node
        Mixed(Parameter(int, 'node_id'), # a dummynet box, or None to delete the entry
              None),
    ]

    returns = Parameter(int, '1 is successful, fault otherwise')

    # Before to create the link we do the following checks:
    #  - node existence,
    #  - dummnet box existence,
    #  - right roles (admin, pi, tech),
    #  - node and dummynet box site should match.

    def call(self, auth, node_id, dummynet_id):

        assert self.caller is not None

        # check for node existence
        # Retrieve nodes from database
        # We do not fetch both node and dummynet
        # since we need to preserve the order of returned objects
        nodes= Nodes(self.api, {'node_id':node_id, 'node_type':'regular'})
        if not nodes:
            raise PLCInvalidArgument, "Node %s not found" % node_id
        node = nodes[0]

        # check for dummynet box existence
        nodes = Nodes(self.api, {'node_id':dummynet_id, 'node_type':'dummynet'})
        if (dummynet_id != None) and not nodes:
            raise PLCInvalidArgument, "Dummynet box %s not found" % dummynet_id

        # check for site matching when create a link
        if (dummynet_id != None):
            dummynet = nodes[0]

            # check if the node and the dummynet_id
            # belong to the same site
            if (node['site_id'] != dummynet['site_id']):
                raise PLCInvalidArgument, \
                      "The Dummynet box must belog to the same site of the Node"

        # check for roles permission to call this method
        if 'admin' not in self.caller['roles']:
            if site not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to manage on this link"

        # Add the dummynetbox
	emulation_link = SetNodeDummynetBox(self.api)
        emulation_link.call(auth, node_id, dummynet_id)

        return 1


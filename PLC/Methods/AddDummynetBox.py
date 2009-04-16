# Add a dummynet box using Accessors
#
# Marta Carbone - unipi
# $Id$

from PLC.Accessors.Accessors_dummynetbox import * # import dummynet accessors
from PLC.Methods.AddNode import AddNode

class AddDummynetBox(AddNode):
    """
    Adds a new dummynetbox, derived class from AddNode class.
    """

    def call(self, auth, site_id_or_login_base, node_fields):
	node_fields.update({'node_type':'dummynet'})
	node_id = AddNode.call(self, auth, site_id_or_login_base, node_fields)

	# create a subclass object to have a handle to issue the call
	subclass = SetNodeSubclass(self.api)
	# set the subclass type
	subclass.call(auth, int(node_id), dbox_subclass)

        return node_id

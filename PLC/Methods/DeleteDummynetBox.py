# Delete a Dummynet box using Accessors
#
# Marta Carbone - unipi
# $Id$
# $URL$

from PLC.Accessors.Accessors_dummynetbox import * # import dummynet accessors
from PLC.Methods.DeleteNode import DeleteNode

class DeleteDummynetBox(DeleteNode):
    """
    Mark an existing dummynetbox as deleted, derived from DeleteNode.
    XXX add type checks
    """

    def call(self, auth, node_id_or_hostname):

        return DeleteNode.call(self, auth, node_id_or_hostname)

#
# Functions for interacting with the node_types table in the database
#
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class NodeType(Row):
    """
    Representation of a row in the node_types table. To use,
    instantiate with a dict of values.
    """

    table_name = 'node_types'
    primary_key = 'node_type'
    join_tables = ['nodes']
    fields = {
        'node_type': Parameter(str, "Node type", max = 20),
        }

    def validate_node_type(self, name):
        # Make sure name is not blank
        if not len(name):
            raise PLCInvalidArgument, "Node type must be specified"

        # Make sure node type does not alredy exist
        conflicts = NodeTypes(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Node type name already in use"

        return name

class NodeTypes(Table):
    """
    Representation of the node_types table in the database.
    """

    def __init__(self, api, node_types = None):
        Table.__init__(self, api, NodeType)

        sql = "SELECT %s FROM node_types" % \
              ", ".join(NodeType.fields)

        if node_types:
            sql += " WHERE node_type IN (%s)" % ", ".join( [ api.db.quote (t) for t in node_types ] )

        self.selectall(sql)

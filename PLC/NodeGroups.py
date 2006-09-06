#
# Functions for interacting with the nodegroups table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table

class NodeGroup(Row):
    """
    Representation of a row in the nodegroups table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with flush().
    """

    fields = {
        'nodegroup_id': Parameter(int, "Node group identifier"),
        'name': Parameter(str, "Node group name"),
        'description': Parameter(str, "Node group description"),
        'is_custom': Parameter(bool, "Is a custom node group (i.e., is not a site node group)")
        }

    # These fields are derived from join tables and are not
    # actually in the nodegroups table.
    join_fields = {
        'node_ids': Parameter([int], "List of nodes in this node group"),
        }

    def __init__(self, api, fields):
        Row.__init__(self, fields)
        self.api = api

    def validate_name(self, name):
        conflicts = NodeGroups(self.api, [name])
        for nodegroup_id in conflicts:
            if 'nodegroup_id' not in self or self['nodegroup_id'] != nodegroup_id:
                raise PLCInvalidArgument, "Node group name already in use"

    def flush(self, commit = True):
        """
        Flush changes back to the database.
        """

        self.validate()

        # Fetch a new nodegroup_id if necessary
        if 'nodegroup_id' not in self:
            rows = self.api.db.selectall("SELECT NEXTVAL('nodegroups_nodegroup_id_seq') AS nodegroup_id")
            if not rows:
                raise PLCDBError, "Unable to fetch new nodegroup_id"
            self['nodegroup_id'] = rows[0]['nodegroup_id']
            insert = True
        else:
            insert = False

        # Filter out fields that cannot be set or updated directly
        fields = dict(filter(lambda (key, value): key in self.fields,
                             self.items()))

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        if insert:
            # Insert new row in nodegroups table
            sql = "INSERT INTO nodegroups (%s) VALUES (%s)" % \
                  (", ".join(keys), ", ".join(values))
        else:
            # Update existing row in sites table
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            sql = "UPDATE nodegroups SET " + \
                  ", ".join(columns) + \
                  " WHERE nodegroup_id = %(nodegroup_id)d"

        self.api.db.do(sql, fields)

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete existing nodegroup from the database.
        """

        assert 'nodegroup_id' in self

        # Delete ourself
        tables = ['nodegroup_nodes', 'override_bootscripts',
                  'conf_assoc', 'node_root_access']

        if self['is_custom']:
            tables.append('nodegroups')
        else:
            # XXX Cannot delete site node groups yet
            pass

        for table in tables:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE nodegroup_id = %(nodegroup_id)" % \
                           table, self)

        if commit:
            self.api.db.commit()

class NodeGroups(Table):
    """
    Representation of row(s) from the nodegroups table in the
    database.
    """

    def __init__(self, api, nodegroup_id_or_name_list = None):
        self.api = api

        # N.B.: Node IDs returned may be deleted.
        sql = "SELECT nodegroups.*, nodegroup_nodes.node_id" \
              " FROM nodegroups" \
              " LEFT JOIN nodegroup_nodes USING (nodegroup_id)"

        if nodegroup_id_or_name_list:
            # Separate the list into integers and strings
            nodegroup_ids = filter(lambda nodegroup_id: isinstance(nodegroup_id, (int, long)),
                                   nodegroup_id_or_name_list)
            names = filter(lambda name: isinstance(name, StringTypes),
                           nodegroup_id_or_name_list)
            sql += " AND (False"
            if nodegroup_ids:
                sql += " OR nodegroup_id IN (%s)" % ", ".join(map(str, nodegroup_ids))
            if names:
                sql += " OR name IN (%s)" % ", ".join(api.db.quote(names)).lower()
            sql += ")"

        rows = self.api.db.selectall(sql)
        for row in rows:
            if self.has_key(row['nodegroup_id']):
                nodegroup = self[row['nodegroup_id']]
                nodegroup.update(row)
            else:
                self[row['nodegroup_id']] = NodeGroup(api, row)

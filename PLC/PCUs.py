#
# Functions for interacting with the pcus table in the database
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

class PCU(Row):
    """
    Representation of a row in the pcu table. To use,
    instantiate with a dict of values.
    """

    fields = {
        'pcu_id': Parameter(int, "Node group identifier"),
        'hostname': Parameter(str, "Fully qualified hostname"),
        }

    # These fields are derived from join tables and are not
    # actually in the pcu table.
    join_fields = {
        'node_ids': Parameter([int], "List of nodes that this PCU controls"),
        }

    def __init__(self, api, fields):
        Row.__init__(self, fields)
        self.api = api

    def flush(self, commit = True):
        """
        Commit changes back to the database.
        """

        self.validate()

        # Fetch a new pcu_id if necessary
        if 'pcu_id' not in self:
            rows = self.api.db.selectall("SELECT NEXTVAL('pcu_pcu_id_seq') AS pcu_id")
            if not rows:
                raise PLCDBError, "Unable to fetch new pcu_id"
            self['pcu_id'] = rows[0]['pcu_id']
            insert = True
        else:
            insert = False

        # Filter out unknown fields
        fields = dict(filter(lambda (key, value): key in self.fields,
                             self.items()))

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        if insert:
            # Insert new row in pcu table
            sql = "INSERT INTO pcu (%s) VALUES (%s)" % \
                  (", ".join(keys), ", ".join(values))
        else:
            # Update existing row in sites table
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            sql = "UPDATE pcu SET " + \
                  ", ".join(columns) + \
                  " WHERE pcu_id = %(pcu_id)d"

        self.api.db.do(sql, fields)

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete existing PCU.
        """

        assert 'pcu_id' in self

        # Delete ourself
        for table in ['pcu_ports', 'pcu']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE nodenetwork_id = %(pcu_id)" % \
                           table, self)

        if commit:
            self.api.db.commit()

class PCUs(Table):
    """
    Representation of row(s) from the pcu table in the
    database.
    """

    def __init__(self, api, pcu_id_or_hostname_list = None):
        self.api = api

        # N.B.: Node IDs returned may be deleted.
        sql = "SELECT pcu.*, pcu_ports.node_id" \
              " FROM pcu" \
              " LEFT JOIN pcu_ports USING (pcu_id)"

        if pcu_id_or_hostname_list:
            # Separate the list into integers and strings
            pcu_ids = filter(lambda pcu_id: isinstance(pcu_id, (int, long)),
                                   pcu_id_or_hostname_list)
            hostnames = filter(lambda hostname: isinstance(hostname, StringTypes),
                           pcu_id_or_hostname_list)
            sql += " AND (False"
            if pcu_ids:
                sql += " OR pcu_id IN (%s)" % ", ".join(map(str, pcu_ids))
            if hostnames:
                sql += " OR hostname IN (%s)" % ", ".join(api.db.quote(hostnames)).lower()
            sql += ")"

        rows = self.api.db.selectall(sql, locals())
        for row in rows:
            if self.has_key(row['pcu_id']):
                pcu = self[row['pcu_id']]
                pcu.update(row)
            else:
                self[row['pcu_id']] = PCU(api, row)

#
# Functions for interacting with the pcus table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.Interfaces import valid_ip, Interface, Interfaces
from PLC.Nodes import Node, Nodes

class PCU(Row):
    """
    Representation of a row in the pcus table. To use,
    instantiate with a dict of values.
    """

    table_name = 'pcus'
    primary_key = 'pcu_id'
    join_tables = ['pcu_node']
    fields = {
        'pcu_id': Parameter(int, "PCU identifier"),
        'site_id': Parameter(int, "Identifier of site where PCU is located"),
        'hostname': Parameter(str, "PCU hostname", max = 254),
        'ip': Parameter(str, "PCU IP address", max = 254),
        'protocol': Parameter(str, "PCU protocol, e.g. ssh, https, telnet", max = 16, nullok = True),
        'username': Parameter(str, "PCU username", max = 254, nullok = True),
        'password': Parameter(str, "PCU username", max = 254, nullok = True),
        'notes': Parameter(str, "Miscellaneous notes", max = 254, nullok = True),
        'model': Parameter(str, "PCU model string", max = 32, nullok = True),
        'node_ids': Parameter([int], "List of nodes that this PCU controls"),
        'ports': Parameter([int], "List of the port numbers that each node is connected to"),
        'last_updated': Parameter(int, "Date and time when node entry was created", ro = True),
        }

    def validate_ip(self, ip):
        if not valid_ip(ip):
            raise PLCInvalidArgument, "Invalid IP address " + ip
        return ip

    validate_last_updated = Row.validate_timestamp

    def update_timestamp(self, col_name, commit = True):
        """
        Update col_name field with current time
        """

        assert 'pcu_id' in self
        assert self.table_name

        self.api.db.do("UPDATE %s SET %s = CURRENT_TIMESTAMP " % (self.table_name, col_name) + \
                       " where pcu_id = %d" % (self['pcu_id']) )
        self.sync(commit)

    def update_last_updated(self, commit = True):
        self.update_timestamp('last_updated', commit)

    def add_node(self, node, port, commit = True):
        """
        Add node to existing PCU.
        """

        assert 'pcu_id' in self
        assert isinstance(node, Node)
        assert isinstance(port, (int, long))
        assert 'node_id' in node

        pcu_id = self['pcu_id']
        node_id = node['node_id']

        if node_id not in self['node_ids'] and port not in self['ports']:
            self.api.db.do("INSERT INTO pcu_node (pcu_id, node_id, port)" \
                           " VALUES(%(pcu_id)d, %(node_id)d, %(port)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].append(node_id)
            self['ports'].append(port)

    def remove_node(self, node, commit = True):
        """
        Remove node from existing PCU.
        """

        assert 'pcu_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        pcu_id = self['pcu_id']
        node_id = node['node_id']

        if node_id in self['node_ids']:
            i = self['node_ids'].index(node_id)
            port = self['ports'][i]

            self.api.db.do("DELETE FROM pcu_node" \
                           " WHERE pcu_id = %(pcu_id)d" \
                           " AND node_id = %(node_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].remove(node_id)
            self['ports'].remove(port)

class PCUs(Table):
    """
    Representation of row(s) from the pcus table in the
    database.
    """

    def __init__(self, api, pcu_filter = None, columns = None):
        Table.__init__(self, api, PCU, columns)

        sql = "SELECT %s FROM view_pcus WHERE True" % \
              ", ".join(self.columns)

        if pcu_filter is not None:
            if isinstance(pcu_filter, (list, tuple, set, int, long)):
                pcu_filter = Filter(PCU.fields, {'pcu_id': pcu_filter})
            elif isinstance(pcu_filter, dict):
                pcu_filter = Filter(PCU.fields, pcu_filter)
            else:
                raise PLCInvalidArgument, "Wrong pcu filter %r"%pcu_filter
            sql += " AND (%s) %s" % pcu_filter.sql(api)

        self.selectall(sql)

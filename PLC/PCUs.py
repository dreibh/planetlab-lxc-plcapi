#
# Functions for interacting with the pcus table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: PCUs.py,v 1.5 2006/10/24 20:02:22 mlhuang Exp $
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.NodeNetworks import valid_ip, NodeNetwork, NodeNetworks
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
        'protocol': Parameter(str, "PCU protocol, e.g. ssh, https, telnet", max = 16),
        'username': Parameter(str, "PCU username", max = 254),
        'password': Parameter(str, "PCU username", max = 254),
        'notes': Parameter(str, "Miscellaneous notes", max = 254),
        'model': Parameter(str, "PCU model string", max = 32),
        'node_ids': Parameter([int], "List of nodes that this PCU controls", ro = True),
        'ports': Parameter([int], "List of the port numbers that each node is connected to", ro = True),
        }

    def validate_ip(self, ip):
        if not valid_ip(ip):
            raise PLCInvalidArgument, "Invalid IP address " + ip
        return ip

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

    def __init__(self, api, pcu_ids = None):
        self.api = api

        # N.B.: Node IDs returned may be deleted.
        sql = "SELECT %s FROM view_pcus" % \
              ", ".join(PCU.fields)

        if pcu_ids:
            sql += " WHERE pcu_id IN (%s)" % ", ".join(map(str, pcu_ids))

        rows = self.api.db.selectall(sql)

        for row in rows:
            self[row['pcu_id']] = pcu = PCU(api, row)
            for aggregate in ['node_ids', 'ports']:
                if not pcu.has_key(aggregate) or pcu[aggregate] is None:
                    pcu[aggregate] = []
                else:
                    pcu[aggregate] = map(int, pcu[aggregate].split(','))

#
# Functions for interacting with the conf_files table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: ConfFiles.py,v 1.2 2006/10/23 20:39:16 mlhuang Exp $
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups

class ConfFile(Row):
    """
    Representation of a row in the conf_files table. To use,
    instantiate with a dict of values.
    """

    table_name = 'conf_files'
    primary_key = 'conf_file_id'
    join_tables = ['conf_file_node', 'conf_file_nodegroup']
    fields = {
        'conf_file_id': Parameter(int, "Configuration file identifier"),
        'enabled': Parameter(bool, "Configuration file is active"),
        'source': Parameter(str, "Relative path on the boot server where file can be downloaded", max = 255),
        'dest': Parameter(str, "Absolute path where file should be installed", max = 255),
        'file_permissions': Parameter(str, "chmod(1) permissions", max = 20),
        'file_owner': Parameter(str, "chown(1) owner", max = 50),
        'file_group': Parameter(str, "chgrp(1) owner", max = 50),
        'preinstall_cmd': Parameter(str, "Shell command to execute prior to installing", max = 1024),
        'postinstall_cmd': Parameter(str, "Shell command to execute after installing", max = 1024),
        'error_cmd': Parameter(str, "Shell command to execute if any error occurs", max = 1024),
        'ignore_cmd_errors': Parameter(bool, "Install file anyway even if an error occurs"),
        'always_update': Parameter(bool, "Always attempt to install file even if unchanged"),
        'node_ids': Parameter(int, "List of nodes linked to this file", ro = True),
        'nodegroup_ids': Parameter(int, "List of node groups linked to this file", ro = True),
        }

    def add_node(self, node, commit = True):
        """
        Add configuration file to node.
        """

        assert 'conf_file_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        conf_file_id = self['conf_file_id']
        node_id = node['node_id']

        if node_id not in self['node_ids']:
            self.api.db.do("INSERT INTO conf_file_node (conf_file_id, node_id)" \
                           " VALUES(%(conf_file_id)d, %(node_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].append(node_id)
            node['conf_file_ids'].append(conf_file_id)

    def remove_node(self, node, commit = True):
        """
        Remove configuration file from node.
        """

        assert 'conf_file_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        conf_file_id = self['conf_file_id']
        node_id = node['node_id']

        if node_id in self['node_ids']:
            self.api.db.do("DELETE FROM conf_file_node" \
                           " WHERE conf_file_id = %(conf_file_id)d" \
                           " AND node_id = %(node_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].remove(node_id)
            node['conf_file_ids'].remove(conf_file_id)

    def add_nodegroup(self, nodegroup, commit = True):
        """
        Add configuration file to node group.
        """

        assert 'conf_file_id' in self
        assert isinstance(nodegroup, NodeGroup)
        assert 'nodegroup_id' in nodegroup

        conf_file_id = self['conf_file_id']
        nodegroup_id = nodegroup['nodegroup_id']

        if nodegroup_id not in self['nodegroup_ids']:
            self.api.db.do("INSERT INTO conf_file_nodegroup (conf_file_id, nodegroup_id)" \
                           " VALUES(%(conf_file_id)d, %(nodegroup_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['nodegroup_ids'].append(nodegroup_id)
            nodegroup['conf_file_ids'].append(conf_file_id)

    def remove_nodegroup(self, nodegroup, commit = True):
        """
        Remove configuration file from node group.
        """

        assert 'conf_file_id' in self
        assert isinstance(nodegroup, NodeGroup)
        assert 'nodegroup_id' in nodegroup

        conf_file_id = self['conf_file_id']
        nodegroup_id = nodegroup['nodegroup_id']

        if nodegroup_id in self['nodegroup_ids']:
            self.api.db.do("DELETE FROM conf_file_nodegroup" \
                           " WHERE conf_file_id = %(conf_file_id)d" \
                           " AND nodegroup_id = %(nodegroup_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['nodegroup_ids'].remove(nodegroup_id)
            nodegroup['conf_file_ids'].remove(conf_file_id)

class ConfFiles(Table):
    """
    Representation of the conf_files table in the database.
    """

    def __init__(self, api, conf_file_ids = None):
        sql = "SELECT %s FROM view_conf_files" % \
              ", ".join(ConfFile.fields)
        
        if conf_file_ids:
            # Separate the list into integers and strings
            sql += " WHERE conf_file_id IN (%s)" % ", ".join(map(str, api.db.quote(conf_file_ids)))

        rows = api.db.selectall(sql)

        for row in rows:
            self[row['conf_file_id']] = ConfFile(api, row)


        for row in rows:
            self[row['conf_file_id']] = conf_file = ConfFile(api, row)
            for aggregate in ['node_ids', 'nodegroup_ids']:
                if not conf_file.has_key(aggregate) or conf_file[aggregate] is None:
                    conf_file[aggregate] = []
                else:
                    conf_file[aggregate] = map(int, conf_file[aggregate].split(','))
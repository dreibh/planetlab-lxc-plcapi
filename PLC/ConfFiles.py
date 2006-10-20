#
# Functions for interacting with the conf_files table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: ConfFiles.py,v 1.4 2006/10/10 21:54:20 mlhuang Exp $
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

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

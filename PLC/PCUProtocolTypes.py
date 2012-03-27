#
# Functions for interacting with the pcu_type_port table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Filter import Filter

class PCUProtocolType(Row):
    """
    Representation of a row in the pcu_protocol_type table. To use,
    instantiate with a dict of values.
    """

    table_name = 'pcu_protocol_type'
    primary_key = 'pcu_protocol_type_id'
    join_tables = []
    fields = {
        'pcu_protocol_type_id': Parameter(int, "PCU protocol type identifier"),
        'pcu_type_id': Parameter(int, "PCU type identifier"),
        'port': Parameter(int, "PCU port"),
        'protocol': Parameter(str, "Protocol"),
        'supported': Parameter(bool, "Is the port/protocol supported by PLC")
        }

    def validate_port(self, port):
        # make sure port is not blank

        if not port:
            raise PLCInvalidArgument, "Port must be specified"

        return port

    def validate_protocol(self, protocol):
        # make sure port is not blank
        if not len(protocol):
            raise PLCInvalidArgument, "protocol must be specified"

        return protocol

class PCUProtocolTypes(Table):
    """
    Representation of the pcu_protocol_types table in the database.
    """

    def __init__(self, api, protocol_type_filter = None, columns = None):
        Table.__init__(self, api, PCUProtocolType, columns)

        sql = "SELECT %s FROM pcu_protocol_type WHERE True" % \
              ", ".join(self.columns)

        if protocol_type_filter is not None:
            if isinstance(protocol_type_filter, (list, tuple, set, int, long)):
                protocol_type_filter = Filter(PCUProtocolType.fields, {'pcu_protocol_type_id': protocol_type_filter})
                sql += " AND (%s) %s" % protocol_type_filter.sql(api, "OR")
            elif isinstance(protocol_type_filter, dict):
                protocol_type_filter = Filter(PCUProtocolType.fields, protocol_type_filter)
                sql += " AND (%s) %s" % protocol_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong pcu_protocol_type filter %r"%protocol_type_filter


        self.selectall(sql)

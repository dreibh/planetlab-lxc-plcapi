#
# Functions for interacting with the pcu_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Filter import Filter

class PCUType(Row):
    """
    Representation of a row in the pcu_types table. To use,
    instantiate with a dict of values.
    """

    table_name = 'pcu_types'
    primary_key = 'pcu_type_id'
    join_tables = ['pcu_protocol_type']
    fields = {
        'pcu_type_id': Parameter(int, "PCU Type Identifier"),
        'model': Parameter(str, "PCU model", max = 254),
        'name': Parameter(str, "PCU full name", max = 254),
        'pcu_protocol_type_ids': Parameter([int], "PCU Protocol Type Identifiers"),
        'pcu_protocol_types': Parameter([dict], "PCU Protocol Type List")
        }

    def validate_model(self, model):
        # Make sure name is not blank
        if not len(model):
            raise PLCInvalidArgument, "Model must be specified"

        # Make sure boot state does not alredy exist
        conflicts = PCUTypes(self.api, [model])
        for pcu_type in conflicts:
            if 'pcu_type_id' not in self or self['pcu_type_id'] != pcu_type['pcu_type_id']:
                raise PLCInvalidArgument, "Model already in use"

        return model

class PCUTypes(Table):
    """
    Representation of the pcu_types table in the database.
    """

    def __init__(self, api, pcu_type_filter = None, columns = None):

        # Remove pcu_protocol_types from query since its not really a field
        # in the db. We will add it later
        if columns == None:
            columns = PCUType.fields.keys()
        if 'pcu_protocol_types' in columns:
            removed_fields = ['pcu_protocol_types']
            columns.remove('pcu_protocol_types')
        else:
            removed_fields = []

        Table.__init__(self, api, PCUType, columns)

        sql = "SELECT %s FROM view_pcu_types WHERE True" % \
              ", ".join(self.columns)

        if pcu_type_filter is not None:
            if isinstance(pcu_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), pcu_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), pcu_type_filter)
                pcu_type_filter = Filter(PCUType.fields, {'pcu_type_id': ints, 'model': strs})
                sql += " AND (%s) %s" % pcu_type_filter.sql(api, "OR")
            elif isinstance(pcu_type_filter, dict):
                pcu_type_filter = Filter(PCUType.fields, pcu_type_filter)
                sql += " AND (%s) %s" % pcu_type_filter.sql(api, "AND")
            elif isinstance (pcu_type_filter, StringTypes):
                pcu_type_filter = Filter(PCUType.fields, {'model':pcu_type_filter})
                sql += " AND (%s) %s" % pcu_type_filter.sql(api, "AND")
            elif isinstance (pcu_type_filter, int):
                pcu_type_filter = Filter(PCUType.fields, {'pcu_type_id':pcu_type_filter})
                sql += " AND (%s) %s" % pcu_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong pcu_type filter %r"%pcu_type_filter


        self.selectall(sql)

         # return a list of protocol type objects for each port type
        if 'pcu_protocol_types' in removed_fields:
            from PLC.PCUProtocolTypes import PCUProtocolTypes
            protocol_type_ids = set()
            for pcu_type in self:
                protocol_type_ids.update(pcu_type['pcu_protocol_type_ids'])

            protocol_return_fields = ['pcu_protocol_type_id', 'port', 'protocol', 'supported']
            all_protocol_types = PCUProtocolTypes(self.api, list(protocol_type_ids), \
                                                  protocol_return_fields).dict('pcu_protocol_type_id')

            for pcu_type in self:
                pcu_type['pcu_protocol_types'] = []
                for protocol_type_id in pcu_type['pcu_protocol_type_ids']:
                    pcu_type['pcu_protocol_types'].append(all_protocol_types[protocol_type_id])

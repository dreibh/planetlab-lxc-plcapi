#
# Functions for interacting with the messages table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Messages.py,v 1.4 2006/10/31 21:46:14 mlhuang Exp $
#

from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class Message(Row):
    """
    Representation of a row in the messages table. 
    """
    
    table_name = 'messages'
    primary_key = 'message_id'
    fields = {
        'message_id': Parameter(str, "Message identifier"),
        'template': Parameter(str, "Message template", nullok = True),
        'enabled': Parameter(bool, "Message is enabled"),
        }
    
class Messages(Table):
    """
    Representation of row(s) from the messages table in the database. 
    """

    def __init__(self, api, message_ids, enabled = None):
        self.api = api
    
        sql = "SELECT %s from messages" % ", ".join(Message.fields)

        if enabled is not None:
            sql += " WHERE enabled IS %(enabled)s"

        rows = self.api.db.selectall(sql, locals())

        for row in rows:
            self[row['message_id']] = Message(api, row)

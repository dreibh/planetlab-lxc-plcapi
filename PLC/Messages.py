#
# Functions for interacting with the messages table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Messages.py,v 1.2 2006/11/08 22:58:23 mlhuang Exp $
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
        Table.__init__(self, api, Message)
    
        sql = "SELECT %s from messages WHERE True" % \
              ", ".join(Message.fields)

	if message_ids:
            sql += " AND message_id IN (%s)" %  ", ".join(map(api.db.quote, message_ids))

        if enabled is not None:
            sql += " AND enabled IS %s" % enabled

        self.selectall(sql)

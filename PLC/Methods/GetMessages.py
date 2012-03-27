from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Messages import Message, Messages
from PLC.Auth import Auth

class GetMessages(Method):
    """
    Returns an array of structs containing details about message
    templates. If message template_filter is specified and is an array
    of message template identifiers, or a struct of message template
    attributes, only message templates matching the filter will be
    returned. If return_fields is specified, only the specified
    details will be returned.
    """

    roles = ['admin', 'node']

    accepts = [
        Auth(),
        Mixed([Message.fields['message_id']],
              Filter(Message.fields)),
        Parameter([str], "List of fields to return", nullok = True),
        ]

    returns = [Message.fields]


    def call(self, auth, message_filter = None, return_fields = None):
        return Messages(self.api, message_filter, return_fields)

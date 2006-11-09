from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter
from PLC.Messages import Message, Messages
from PLC.Auth import Auth

class GetMessages(Method):
    """
    Return an array of structs containing details about message
    templates. If message_ids is specified, only the specified
    messages will be queried.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        [Message.fields['message_id']],
        ]

    returns = [Message.fields]

    event_type = 'Get'
    object_type = 'Message'
    object_ids = []

    def call(self, auth, message_ids = None):
        return Messages(self.api, message_ids)

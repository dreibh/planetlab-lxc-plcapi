from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter
from PLC.Messages import Message, Messages
from PLC.Auth import Auth

class AddMessage(Method):
    """
    Adds a new message template. Any values specified in
    message_fields are used, otherwise defaults are used.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Message.fields,
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, message_fields):
        message = Message(self.api, message_fields)
        message.sync(insert = True)

        return 1

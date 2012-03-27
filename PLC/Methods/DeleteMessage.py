from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Messages import Message, Messages
from PLC.Auth import Auth

class DeleteMessage(Method):
    """
    Deletes a message template.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Message.fields['message_id'],
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, message_id):
        # Get message information
        messages = Messages(self.api, [message_id])
        if not messages:
            raise PLCInvalidArgument, "No such message"
        message = messages[0]

        message.delete()
        self.event_objects = {'Message': [message['message_id']]}

        return 1

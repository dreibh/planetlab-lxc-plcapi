from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Messages import Message, Messages
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['template', 'enabled']

class UpdateMessage(Method):
    """
    Updates the parameters of an existing message template with the
    values in message_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    message_fields = dict(filter(can_update, Message.fields.items()))

    accepts = [
        Auth(),
        Message.fields['message_id'],
        message_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, message_id, message_fields):
        message_fields = dict(filter(can_update, message_fields.items()))

        # Get message information
        messages = Messages(self.api, [message_id])
        if not messages:
            raise PLCInvalidArgument, "No such message"
        message = messages[0]

        message.update(message_fields)
        message.sync()
        self.event_objects = {'Message': [message['message_id']]}

        return 1

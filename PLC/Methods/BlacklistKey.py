from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import Auth

class BlacklistKey(Method):
    """
    Blacklists a key, disassociating it and all others identical to it
    from all accounts and preventing it from ever being added again.

    WARNING: Identical keys associated with other accounts with also
    be blacklisted.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Key.fields['key_id'],
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, key_id):
        # Get associated key details
        keys = Keys(self.api, [key_id])
        if not keys:
            raise PLCInvalidArgument, "No such key"
        key = keys[0]

        # N.B.: Can blacklist any key, even foreign ones

        key.blacklist()

        # Logging variables
        self.event_objects = {'Key': [key['key_id']]}
        self.message = 'Key %d blacklisted' % key['key_id']

        return 1

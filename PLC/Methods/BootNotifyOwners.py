from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth, BootAuth
from PLC.Messages import Message, Messages
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites

class BootNotifyOwners(Method):
    """
    Notify the owners of the node, and/or support about an event that
    happened on the machine.

    Returns 1 if successful.
    """

    roles = ['node']

    accepts = [
        BootAuth(),
        Message.fields['message_id'],
        Parameter(int, "Notify PIs"),
        Parameter(int, "Notify technical contacts"),
        Parameter(int, "Notify support")
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, message_id, include_pis, include_techs, include_support):
        messages = Messages(self.api, [message_id], enabled = True).values()
        if not messages:
            raise PLCInvalidArgument, "No such message template"

        if not self.api.config.PLC_MAIL_ENABLED:
            return 1

        recipients = {}

        if self.api.config.PLC_MAIL_BOOT_ADDRESS:
            recipients[self.api.config.PLC_MAIL_BOOT_ADDRESS] = "Boot Messages"

        if include_support and self.api.config.PLC_MAIL_SUPPORT_ADDRESS:
            recipients[self.api.config.PLC_MAIL_SUPPORT_ADDRESS] = self.api.config.PLC_NAME + " Support"

        if include_pis or include_techs:
            sites = Sites(self.api, [self.caller['site_id']]).values()
            if not sites:
                raise PLCAPIError, "No site associated with node"
            site = sites[0]

            persons = Persons(self.api, site['person_ids']).values()
            for person in persons:
                if include_pis and 'pi' in person['roles'] or \
                   include_techs and 'tech' in person['roles']:
                    recipients[person['email']] = person['first_name'] + " " + person['last_name']

        # XXX Send mail

        return 1
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.sendmail import sendmail

class NotifySupport(Method):
    """
    Sends an e-mail message to the configured support address.

    Returns 1 if successful.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Parameter(str, "E-mail subject"),
        Parameter(str, "E-mail body")
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, subject, body):
        to_name="%s Support"%self.api.config.PLC_NAME
        to_address=self.api.config.PLC_MAIL_SUPPORT_ADDRESS

        # Send email
        sendmail(self.api, To=(to_name,to_address),
                 Subject = subject,
                 Body = body)

        # Logging variables
        #self.event_objects = {'Person': [person['person_id'] for person in persons]}
        self.message = subject

        return 1

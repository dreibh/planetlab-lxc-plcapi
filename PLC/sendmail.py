import smtplib
import string
import sys
import time

from PLC.Faults import *

"""
used to send out emails - sets up the headers correctly
"""
class sendmail:

    def __init__(self, config):

	self.MAIL_ENABLED = config.PLC_MAIL_ENABLED

        self.SMTP_SERVER= 'localhost'
    
        self.X_MAILER= 'PlanetLab API Mailer'


    """
    open up a connect to our mail server, and send out a message.

    the email addresses are not verified before sending out the message.

    to_addr_list, cc_addr_list, and from_addr should be a dictionary, with the keys
    being the email address and the value being the plain text name of
    the recipient. only the first key from from_addr will be used, so it should
    contain only one address.

    subject is not checked for multiple lines - ensure it is only one.
    """
    def mail( self, to_addr_list, cc_addr_list, from_addr, subject, content ):

	if self.MAIL_ENABLED == 0:
            return 1
        
        server= smtplib.SMTP(self.SMTP_SERVER)

        str_date= time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())

        str_from_addr= self.create_recipient_list(from_addr,1)
        str_to_addr= self.create_recipient_list(to_addr_list)

        full_message  = ""
        full_message += "Content-type: text/plain; charset=iso-8859-1\r\n"
        full_message += "Date: %s\r\n" % str_date
        full_message += "MIME-Version: 1.0\r\n"

        full_message += "To: %s\r\n" % str_to_addr
        full_message += "From: %s\r\n" % str_from_addr
        
        if cc_addr_list is not None and len(cc_addr_list) > 0:
            str_cc_addr= self.create_recipient_list(cc_addr_list)
            full_message += "Cc: %s\r\n" % str_cc_addr

        full_message += "Subject: %s\r\n" % subject
        full_message += "Reply-To: %s\r\n" % str_from_addr
        full_message += "X-Mailer: %s\r\n\r\n" % self.X_MAILER        
        full_message += content

        try:
            # get just a list of to recipients (needed for envelope). this
            # needs to include all reciepients, including Cc
            local_to_list= to_addr_list.copy()

            if cc_addr_list is not None:
                local_to_list.update( cc_addr_list )
                
            all_to_addr_list= self.create_recipient_list(local_to_list,
                                                         return_string=0)
            
            # send out the mail!
	    rc= server.sendmail(str_from_addr, all_to_addr_list, full_message )

	    return 1
        
        except smtplib.SMTPRecipientsRefused, err:
            sys.stderr.write( "SMTPRecipientsRefused: %s" % repr(err) )
            return 0
        
        except smtplib.SMTPHeloError:
            sys.stderr.write( "SMTPHeloError: %s" % repr(err) )
            return 0
        
        except smtplib.SMTPSenderRefused:
            sys.stderr.write( "SMTPSenderRefused: %s" % repr(err) )
            return 0
        
        except smtplib.SMTPDataError:
            sys.stderr.write( "SMTPDataError: %s" % repr(err) )
            return 0
        




    """
    accepts a list of email recipient as a dictionary in the same format
    as the mail function, and returns it in a format suitable for use in
    an email message. for example:

    if limit is specified, only limit number of entries from
    addr_list is used. which one is used is not defined, so it is really only
    useful to make sure that the result has a single entry (for from lines)

    for return_string= 1:
      input: {'user@domain.com': 'A User','test@planet-lab.org': 'PL User'}
      ouput: 'A User <user@domain.com>, PL User <test@planet-lab.org>'
    otherwise:
      input: {'user@domain.com': 'A User','test@planet-lab.org': 'PL User'}
      ouput: ['A User <user@domain.com>', 'PL User <test@planet-lab.org>']
  
    """
    def create_recipient_list( self, addr_list, return_string= 1, limit= None ):
        if not isinstance(addr_list,dict):
            raise PLCAPIError, \
                  "Internal error, call to create_recipient_list " \
                  "with non-dict addr_list (%s)." % str(addr_list)
        
        if limit == None:
            limit= len(addr_list.keys())

        if limit <= 0:
            return ''

        recipients= []
        total= 0
        
        for email in addr_list.keys():
            recipients = recipients + ['%s <%s>' % (addr_list[email],email)]
            total= total+1
            if total == limit:
                break

        if return_string == 1:
            return string.join( recipients, ", " )
        else:
            return recipients

    
        
            

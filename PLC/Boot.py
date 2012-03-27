#
# Boot Manager support
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2007 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Debug import log
from PLC.Messages import Message, Messages
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.sendmail import sendmail

def notify_owners(method, node, message_id,
                  include_pis = False, include_techs = False, include_support = False,
                  fault = None):
    messages = Messages(method.api, [message_id], enabled = True)
    if not messages:
        print >> log, "No such message template '%s'" % message_id
        return 1
    message = messages[0]

    To = []

    if method.api.config.PLC_MAIL_BOOT_ADDRESS:
        To.append(("Boot Messages", method.api.config.PLC_MAIL_BOOT_ADDRESS))

    if include_support and method.api.config.PLC_MAIL_SUPPORT_ADDRESS:
        To.append(("%s Support" % method.api.config.PLC_NAME,
                   method.api.config.PLC_MAIL_SUPPORT_ADDRESS))

    if include_pis or include_techs:
        sites = Sites(method.api, [node['site_id']])
        if not sites:
            raise PLCAPIError, "No site associated with node"
        site = sites[0]

        persons = Persons(method.api, site['person_ids'])
        for person in persons:
            if (include_pis and 'pi' in person['roles'] and person['enabled']) or \
               (include_techs and 'tech' in person['roles'] and person['enabled']) :
                To.append(("%s %s" % (person['first_name'], person['last_name']), person['email']))

    # Send email
    params = {'node_id': node['node_id'],
              'hostname': node['hostname'],
              'PLC_WWW_HOST': method.api.config.PLC_WWW_HOST,
              'PLC_WWW_SSL_PORT': method.api.config.PLC_WWW_SSL_PORT,
              'fault': fault}

    sendmail(method.api, To = To,
             Subject = message['subject'] % params,
             Body = message['template'] % params)

    # Logging variables
    method.object_type = "Node"
    method.object_ids = [node['node_id']]
    method.message = "Sent message %s" % message_id

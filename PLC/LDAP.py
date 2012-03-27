#
# LDAP interface. 
# Tony Mack  <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

import ldap
import traceback
from PLC.Debug import profile, log
from PLC.Faults import *


class LDAP:
    def __init__(self, api):
        self.api = api
        self.debug = False
#        self.debug = True
        self.connection = None
        self.async = False

    def bind(self, async=False):
        self.async = async
        if self.connection is None:
            try:
                if self.api.config.PLC_LDAP_SECURE:
                    url = 'ldaps://%s' % \
                          (self.api.config.PLC_LDAP_HOST, self.api.config.PLC_LDAP_PORT)
                else:
                    url = 'ldap://%s' % \
                           (self.api.config.PLC_LDAP_HOST, self.api.config.PLC_LDAP_PORT)
                self.connection = ldap.open(url)
                dn = self.api.config.PLC_LDAP_ROOT_DN
                pw = self.api.config.PLC_LDAP_ROOT_PASSWORD
                if async:
                   self.connection.bind(dn, pw, ldap.AUTH_SIMPLE)
                else:
                   self.connection.bind_s(dn, pw, ldap.AUTH_SIMPLE)
            except ldap.LDAPError, e:
                raise PLCLDAPError, "Unable to bind to server: %s" % e
        return connection 

    def close(self):
        """
        Close the connection
        """
        if self.connection is not None:
            self.connection.unbind()
            self.connection = None

    def pl_to_ldap(self, filter):
        """
        Convert pl fields to ldap fields     
        """
        ldap_filter = {'objectClass': '*'}
        if 'first_name' in filter and 'last_name' in filter:
            ldap_filter['cn'] = "%s %s" % \
                    (filter['first_name'], filter['last_name'])
        for key in filter:
            if key == 'email':
                ldap_filter['mail'] = filter['email']
            if key ==  'objectClass':
                ldap_filter['objectClass'] = filter['objectClass']     
             
        return ldap_filter

    def to_ldap_filter(search_filter):
        search_filter = pl_to_ldap(search_filter) 
        values = []
        for (key,value) in search_filter.items():
            values.append("(%s=%s)" % (key,value))
        
        return "(&%s)" % "".join(values)        

    def to_list_of_dicts(results_list):
        """
        Convert ldap search results to a list of dicts
        """
        results = []
        for (dn, result_dict) in result_list:
            result_dict['dn'] = dn
            results.append(result_dict)
        return results            
            
    def search(self, search_filter):
        """
        Search the ldap directory
        """
        self.bind()
        dn = self.api.config.PLC_LDAP_SUFFIX
        scope = ldap.SCOPE_SUBTREE
        filter = to_ldap_filter(search_filter)
        # always do synchronous searchers
        search = self.connection.search_s
        results = to_list_of_dicts(search(dn, scope, filter))
        self.close()
        return results

    def add(self, record, type):
        """
        Add to the ldap directory  
        """
        self.bind()
        self.close()
        
    def update(self, record):
        """
        Update a record in the ldap directory        
        """
        self.bind()
        self.close()
    
    def remove(self, record):
        """
        Remove a record from the ldap directory
        """       
        self.bind()
        self.close()

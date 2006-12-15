#
# Thierry Parmentelat - INRIA
# 

import re
from types import StringTypes
from urlparse import urlparse

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Table import Row, Table
import PLC.Auth

from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.Nodes import Node, Nodes
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Slices import Slice, Slices

import xmlrpclib
from PLC.PyCurl import PyCurlTransport
from PLC.GPG import gpg_sign

class Peer(Row):
    """
    Stores the list of peering PLCs in the peers table. 
    See the Row class for more details
    """

    table_name = 'peers'
    primary_key = 'peer_id'
    fields = {
	'peer_id': Parameter (int, "Peer identifier"),
	'peername': Parameter (str, "Peer name"),
	'peer_url': Parameter (str, "Peer API URL"),
	'key': Parameter(str, "Peer GPG public key"),
	'cacert': Parameter(str, "Peer SSL public certificate"),
        ### cross refs
        'site_ids': Parameter([int], "List of sites for this peer is authoritative"),
        'person_ids': Parameter([int], "List of users for this peer is authoritative"),
        'key_ids': Parameter([int], "List of keys for which this peer is authoritative"),
        'node_ids': Parameter([int], "List of nodes for which this peer is authoritative"),
        'attribute_type_ids': Parameter([int], "List of slice attribute types for which this peer is authoritative"),
        'slice_attribute_ids': Parameter([int], "List of slice attributes for which this peer is authoritative"),
        'slice_ids': Parameter([int], "List of slices for which this peer is authoritative"),
	}

    def validate_peer_url(self, url):
	"""
	Validate URL. Must be HTTPS.
	"""

        (scheme, netloc, path, params, query, fragment) = urlparse(url)
        if scheme != "https":
            raise PLCInvalidArgument, "Peer URL scheme must be https"

	return url

    def delete(self, commit = True):
	"""
	Deletes this peer and all related entities.
	"""

	assert 'peer_id' in self

        # Remove all related entities
        for obj in \
                Sites(self.api, self['site_ids']) + \
                Persons(self.api, self['person_ids']) + \
                Keys(self.api, self['key_ids']) + \
                Nodes(self.api, self['node_ids']) + \
                SliceAttributeTypes(self.api, self['attribute_type_ids']) + \
                SliceAttributes(self.api, self['slice_attribute_ids']) + \
                Slices(self.api, self['slice_ids']):
            assert obj['peer_id'] == self['peer_id']
            obj.delete(commit = False)

        # Mark as deleted
	self['deleted'] = True
	self.sync(commit)

    def connect(self, **kwds):
        """
        Connect to this peer via XML-RPC.
        """

        self.server = xmlrpclib.ServerProxy(self['peer_url'],
                                            PyCurlTransport(self['peer_url'], self['cacert']),
                                            allow_none = 1, **kwds)

    def add_auth(self, function, methodname, **kwds):
        """
        Sign the specified XML-RPC call and add an auth struct as the
        first argument of the call.
        """

        def wrapper(*args, **kwds):
            signature = gpg_sign(methodname, args,
                                 self.api.config.PLC_ROOT_GPG_KEY,
                                 self.api.config.PLC_ROOT_GPG_KEY_PUB)

            auth = {'AuthMethod': "gpg",
                    'name': self.api.config.PLC_NAME,
                    'signature': signature}

            # Automagically add auth struct to every call
            args = (auth,) + args

            return function(*args)

        return wrapper

    def __getattr__(self, methodname):
        """
        Fetch a callable for the specified method.
        """

        function = getattr(self.server, methodname)

        try:
            # Figure out if the function is a PLCAPI function and
            # requires an authentication structure as its first
            # argument.
            api_function = self.api.callable(methodname)
            if api_function.accepts and \
               (isinstance(api_function.accepts[0], PLC.Auth.Auth) or \
                (isinstance(api_function.accepts[0], Mixed) and \
                 filter(lambda param: isinstance(param, Auth), func.accepts[0]))):
                function = self.add_auth(function, methodname)
        except Exception, err:
            pass

        return function

class Peers (Table):
    """ 
    Maps to the peers table in the database
    """
    
    def __init__ (self, api, peer_filter = None, columns = None):
        Table.__init__(self, api, Peer, columns)

	sql = "SELECT %s FROM view_peers WHERE deleted IS False" % \
              ", ".join(self.columns)

        if peer_filter is not None:
            if isinstance(peer_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), peer_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), peer_filter)
                peer_filter = Filter(Peer.fields, {'peer_id': ints, 'peername': strs})
                sql += " AND (%s)" % peer_filter.sql(api, "OR")
            elif isinstance(peer_filter, dict):
                peer_filter = Filter(Peer.fields, peer_filter)
                sql += " AND (%s)" % peer_filter.sql(api, "AND")

	self.selectall(sql)

#
# Thierry Parmentelat - INRIA
# 

import re
from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Table import Row, Table
import PLC.Auth

from PLC.Nodes import Nodes,Node
from PLC.Slices import Slices,Slice

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
	'peer_id' : Parameter (int, "Peer identifier"),
	'peername' : Parameter (str, "Peer name"),
	'peer_url' : Parameter (str, "Peer API url"),
	'key': Parameter(str, "Peer GPG public key"),
	'cacert': Parameter(str, "Peer SSL public certificate"),
        ### cross refs
        'site_ids' : Parameter ([int], "This peer's sites ids"),
        'person_ids' : Parameter ([int], "This peer's persons ids"),
	'node_ids' : Parameter ([int], "This peer's nodes ids"),
	'slice_ids' : Parameter ([int], "This peer's slices ids"),
	}

    def validate_peer_url (self, url):
	"""
	Validate URL, checks it looks like https 
	"""
	invalid_url = PLCInvalidArgument("Invalid URL")
	if not re.compile ("^https://.*$").match(url) : 
	    raise invalid_url
	return url

    def delete (self, commit=True):
	"""
	Delete peer
	"""
	
	assert 'peer_id' in self

        # remove nodes depending on this peer
        for foreign_node in Nodes (self.api, self['node_ids']):
            foreign_node.delete(commit)

        # remove the peer
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

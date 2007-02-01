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

class Peer(Row):
    """
    Stores the list of peering PLCs in the peers table. 
    See the Row class for more details
    """

    table_name = 'peers'
    primary_key = 'peer_id'
    join_tables = ['peer_site', 'peer_person', 'peer_key', 'peer_node',
                   'peer_slice_attribute_type', 'peer_slice_attribute', 'peer_slice']
    fields = {
	'peer_id': Parameter (int, "Peer identifier"),
	'peername': Parameter (str, "Peer name"),
	'peer_url': Parameter (str, "Peer API URL"),
	'key': Parameter(str, "Peer GPG public key"),
	'cacert': Parameter(str, "Peer SSL public certificate"),
        ### cross refs
        'site_ids': Parameter([int], "List of sites for which this peer is authoritative"),
        'person_ids': Parameter([int], "List of users for which this peer is authoritative"),
        'key_ids': Parameter([int], "List of keys for which this peer is authoritative"),
        'node_ids': Parameter([int], "List of nodes for which this peer is authoritative"),
        'slice_ids': Parameter([int], "List of slices for which this peer is authoritative"),
	}

    def validate_peername(self, peername):
        if not len(peername):
            raise PLCInvalidArgument, "Peer name must be specified"

        conflicts = Peers(self.api, [peername])
        for peer in conflicts:
            if 'peer_id' not in self or self['peer_id'] != peer['peer_id']:
                raise PLCInvalidArgument, "Peer name already in use"

        return peername

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
            Slices(self.api, self['slice_ids']) + \
            Keys(self.api, self['key_ids']) + \
            Persons(self.api, self['person_ids']) + \
            Nodes(self.api, self['node_ids']) + \
            Sites(self.api, self['site_ids']):
            assert obj['peer_id'] == self['peer_id']
            obj.delete(commit = False)

        # Mark as deleted
	self['deleted'] = True
	self.sync(commit)

    def add_site(self, site, peer_site_id, commit = True):
        """
        Associate a local site entry with this peer.
        """

        add = Row.add_object(Site, 'peer_site')
        add(self, site,
            {'peer_id': self['peer_id'],
             'site_id': site['site_id'],
             'peer_site_id': peer_site_id},
            commit = commit)

    def add_person(self, person, peer_person_id, commit = True):
        """
        Associate a local user entry with this peer.
        """

        add = Row.add_object(Person, 'peer_person')
        add(self, person,
            {'peer_id': self['peer_id'],
             'person_id': person['person_id'],
             'peer_person_id': peer_person_id},
            commit = commit)

    def add_key(self, key, peer_key_id, commit = True):
        """
        Associate a local key entry with this peer.
        """

        add = Row.add_object(Key, 'peer_key')
        add(self, key,
            {'peer_id': self['peer_id'],
             'key_id': key['key_id'],
             'peer_key_id': peer_key_id},
            commit = commit)

    def add_node(self, node, peer_node_id, commit = True):
        """
        Associate a local node entry with this peer.
        """

        add = Row.add_object(Node, 'peer_node')
        add(self, node,
            {'peer_id': self['peer_id'],
             'node_id': node['node_id'],
             'peer_node_id': peer_node_id},
            commit = commit)

    def add_slice(self, slice, peer_slice_id, commit = True):
        """
        Associate a local slice entry with this peer.
        """

        add = Row.add_object(Slice, 'peer_slice')
        add(self, slice,
            {'peer_id': self['peer_id'],
             'slice_id': slice['slice_id'],
             'peer_slice_id': peer_slice_id},
            commit = commit)

    def connect(self, **kwds):
        """
        Connect to this peer via XML-RPC.
        """

        import xmlrpclib
        from PLC.PyCurl import PyCurlTransport
        self.server = xmlrpclib.ServerProxy(self['peer_url'],
                                            PyCurlTransport(self['peer_url'], self['cacert']),
                                            allow_none = 1, **kwds)

    def add_auth(self, function, methodname, **kwds):
        """
        Sign the specified XML-RPC call and add an auth struct as the
        first argument of the call.
        """

        def wrapper(*args, **kwds):
            from PLC.GPG import gpg_sign
            signature = gpg_sign(args,
                                 self.api.config.PLC_ROOT_GPG_KEY,
                                 self.api.config.PLC_ROOT_GPG_KEY_PUB,
                                 methodname)

            auth = {'AuthMethod': "gpg",
                    'name': self.api.config.PLC_NAME,
                    'signature': signature}

            # Automagically add auth struct to every call
            args = (auth,) + args

            return function(*args)

        return wrapper

    def __getattr__(self, attr):
        """
        Returns a callable API function if attr is the name of a
        PLCAPI function; otherwise, returns the specified attribute.
        """

        try:
            # Figure out if the specified attribute is the name of a
            # PLCAPI function. If so and the function requires an
            # authentication structure as its first argument, return a
            # callable that automagically adds an auth struct to the
            # call.
            methodname = attr
            api_function = self.api.callable(methodname)
            if api_function.accepts and \
               (isinstance(api_function.accepts[0], PLC.Auth.Auth) or \
                (isinstance(api_function.accepts[0], Mixed) and \
                 filter(lambda param: isinstance(param, Auth), api_function.accepts[0]))):
                function = getattr(self.server, methodname)
                return self.add_auth(function, methodname)
        except Exception, err:
            pass

        if hasattr(self, attr):
            return getattr(self, attr)
        else:
            raise AttributeError, "type object 'Peer' has no attribute '%s'" % attr

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

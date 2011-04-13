#
# Thierry Parmentelat - INRIA
#

import re
from types import StringTypes
import traceback
from urlparse import urlparse

import PLC.Auth
from PLC.Debug import log
from PLC.Faults import *
from PLC.Namespace import hostname_to_hrn
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagType, TagTypes
from PLC.NodeTags import NodeTag, NodeTags
from PLC.SliceTags import SliceTag, SliceTags
from PLC.Slices import Slice, Slices

class Peer(Row):
    """
    Stores the list of peering PLCs in the peers table.
    See the Row class for more details
    """

    table_name = 'peers'
    primary_key = 'peer_id'
    join_tables = ['peer_site', 'peer_person', 'peer_key', 'peer_node', 'peer_slice']
    fields = {
        'peer_id': Parameter (int, "Peer identifier"),
        'peername': Parameter (str, "Peer name"),
        'peer_url': Parameter (str, "Peer API URL"),
        'key': Parameter(str, "Peer GPG public key"),
        'cacert': Parameter(str, "Peer SSL public certificate"),
        'shortname' : Parameter(str, "Peer short name"),
        'hrn_root' : Parameter(str, "Root of this peer in a hierarchical naming space"),
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
        if path[-1] != '/':
            raise PLCInvalidArgument, "Peer URL should end with /"

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

    def remove_site(self, site, commit = True):
        """
        Unassociate a site with this peer.
        """

        remove = Row.remove_object(Site, 'peer_site')
        remove(self, site, commit)

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

    def remove_person(self, person, commit = True):
        """
        Unassociate a site with this peer.
        """

        remove = Row.remove_object(Person, 'peer_person')
        remove(self, person, commit)

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

    def remove_key(self, key, commit = True):
        """
        Unassociate a key with this peer.
        """

        remove = Row.remove_object(Key, 'peer_key')
        remove(self, key, commit)

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

        sites = Sites(self.api, node['site_id'], ['login_base'])
        site = sites[0]
        login_base = site['login_base']
        try:
            # attempt to manually update the 'hrn' tag with the remote prefix
            hrn_root = self['hrn_root']
            hrn = hostname_to_hrn(hrn_root, login_base, node['hostname'])
            tags = {'hrn': hrn}
            Node(self.api, node).update_tags(tags)
        except:
            print >>log, "WARNING: (beg) could not find out hrn on hostname=%s"%node['hostname']
            traceback.print_exc(5,log)
            print >>log, "WARNING: (end) could not find out hrn on hostname=%s"%node['hostname']

    def remove_node(self, node, commit = True):
        """
        Unassociate a node with this peer.
        """

        remove = Row.remove_object(Node, 'peer_node')
        remove(self, node, commit)
        # attempt to manually update the 'hrn' tag now that the node is local
        root_auth = self.api.config.PLC_HRN_ROOT
        sites = Sites(self.api, node['site_id'], ['login_base'])
        site = sites[0]
        login_base = site['login_base']
        hrn = hostname_to_hrn(root_auth, login_base, node['hostname'])
        tags = {'hrn': hrn}
        Node(self.api, node).update_tags(tags)

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

    def remove_slice(self, slice, commit = True):
        """
        Unassociate a slice with this peer.
        """

        remove = Row.remove_object(Slice, 'peer_slice')
        remove(self, slice, commit)

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
                sql += " AND (%s) %s" % peer_filter.sql(api, "OR")
            elif isinstance(peer_filter, dict):
                peer_filter = Filter(Peer.fields, peer_filter)
                sql += " AND (%s) %s" % peer_filter.sql(api, "AND")
            elif isinstance(peer_filter, (int, long)):
                peer_filter = Filter(Peer.fields, {'peer_id': peer_filter})
                sql += " AND (%s) %s" % peer_filter.sql(api, "AND")
            elif isinstance(peer_filter, StringTypes):
                peer_filter = Filter(Peer.fields, {'peername': peer_filter})
                sql += " AND (%s) %s" % peer_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong peer filter %r"%peer_filter

        self.selectall(sql)

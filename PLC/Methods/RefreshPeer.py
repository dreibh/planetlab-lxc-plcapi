#
# Thierry Parmentelat - INRIA
# 
# $Id$

import time

from PLC.Debug import log
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.KeyTypes import KeyType, KeyTypes
from PLC.Keys import Key, Keys
from PLC.BootStates import BootState, BootStates
from PLC.Nodes import Node, Nodes
from PLC.SliceInstantiations import SliceInstantiations
from PLC.Slices import Slice, Slices

verbose=False

# initial version was doing only one final commit
# * set commit_mode to False to get that behaviour
# * set comit_mode to True to get everything synced at once
commit_mode=True

def message (to_print=None,verbose_only=False):
    if verbose_only and not verbose:
        return
    print >> log, time.strftime("%m-%d-%H-%M-%S:"),
    if to_print:
        print >>log, to_print

def message_verbose(to_print=None):
    message(to_print,verbose_only=True)

class RefreshPeer(Method):
    """
    Fetches site, node, slice, person and key data from the specified peer
    and caches it locally; also deletes stale entries.
    Upon successful completion, returns a dict reporting various timers.
    Faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Peer.fields['peer_id'],
              Peer.fields['peername']),
        ]

    returns = Parameter(int, "1 if successful")

    def call(self, auth, peer_id_or_peername):
        # Get peer
	peers = Peers(self.api, [peer_id_or_peername])
        if not peers:
            raise PLCInvalidArgument, "No such peer '%s'" % unicode(peer_id_or_peername)
        peer = peers[0]
        peer_id = peer['peer_id']

	# Connect to peer API
        peer.connect()

        timers = {}

        # Get peer data
        start = time.time()
	message('RefreshPeer starting up (commit_mode=%r)'%commit_mode)
	message('Issuing GetPeerData')
        peer_tables = peer.GetPeerData()
        # for smooth federation with 4.2 - ignore fields that are useless anyway, and rewrite boot_state
        boot_state_rewrite={'dbg':'safeboot','diag':'safeboot','disable':'disabled',
                            'inst':'reinstall','rins':'reinstall','new':'reinstall','rcnf':'reinstall'}
        for node in peer_tables['Nodes']:
            for key in ['nodenetwork_ids','dummybox_id']:
                if key in node:
                    del node[key]
            if node['boot_state'] in boot_state_rewrite: node['boot_state']=boot_state_rewrite[node['boot_state']]
        for slice in peer_tables['Slices']:
            for key in ['slice_attribute_ids']:
                if key in slice:
                    del slice[key]
        timers['transport'] = time.time() - start - peer_tables['db_time']
        timers['peer_db'] = peer_tables['db_time']
        message_verbose('GetPeerData returned -> db=%d transport=%d'%(timers['peer_db'],timers['transport']))

        def sync(objects, peer_objects, classobj):
            """
            Synchronizes two dictionaries of objects. objects should
            be a dictionary of local objects keyed on their foreign
            identifiers. peer_objects should be a dictionary of
            foreign objects keyed on their local (i.e., foreign to us)
            identifiers. Returns a final dictionary of local objects
            keyed on their foreign identifiers.
            """

            classname=classobj(self.api).__class__.__name__
            message_verbose('Entering sync on %s'%classname)

            synced = {}

            # Delete stale objects
            for peer_object_id, object in objects.iteritems():
                if peer_object_id not in peer_objects:
                    object.delete(commit = commit_mode)
                    message("%s %s %s deleted"%(peer['peername'],classname, object[object.primary_key]))

            total = len(peer_objects)
            count=1
            # set this to something realistic to trace down a given object(s)
            trace_type="Node"
            trace_ids=[]
            def trace (message):
                if classname == trace_type and peer_object_id in trace_ids:
                    message_verbose('TRACE>>'+message)
                
            # Add/update new/existing objects
            for peer_object_id, peer_object in peer_objects.iteritems():
                message_verbose ('DBG %s peer_object_id=%d (%d/%d)'%(classname,peer_object_id,count,total))
                count += 1
                if classname == 'Node':
                    message_verbose ('DBG>> hostname=%s'%peer_object['hostname'])
                elif classname == "Slice":
                    message_verbose ('DBG>> slicename=%s'%peer_object['name'])
                if peer_object_id in objects:
                    # Update existing object
                    object = objects[peer_object_id]

                    # Replace foreign identifier with existing local
                    # identifier temporarily for the purposes of
                    # comparison.
                    peer_object[object.primary_key] = object[object.primary_key]

                    # Must use __eq__() instead of == since
                    # peer_object may be a raw dict instead of a Peer
                    # object.
                    trace ("in objects : comparing")
                    if not object.__eq__(peer_object):
                        # Only update intrinsic fields
                        trace ("updating")
                        object.update(object.db_fields(peer_object))
                        trace ("updated")
                        sync = True
                        dbg = "changed"
                    else:
                        trace ("intact")
                        sync = False
                        dbg = None

                    # Restore foreign identifier
                    peer_object[object.primary_key] = peer_object_id
                else:
                    trace ("not in objects -- creating")
                    # Add new object
                    object = classobj(self.api, peer_object)
                    trace ("created")
                    # Replace foreign identifier with new local identifier
                    del object[object.primary_key]
                    trace ("forced clean id")
                    sync = True
                    dbg = "added"

                if sync:
                    message_verbose("DBG>> syncing %s %d - commit_mode=%r"%(classname,peer_object_id,commit_mode))
                    try:
                        object.sync(commit = commit_mode)
                    except PLCInvalidArgument, err:
                        # Skip if validation fails
                        # XXX Log an event instead of printing to logfile
                        message("Warning: %s Skipping invalid %s %r : %r"%(\
                                peer['peername'], classname, peer_object, err))
                        continue

                synced[peer_object_id] = object

                if dbg:
                    message("%s: %s %d %s"%(peer['peername'], classname, object[object.primary_key], dbg))

            message_verbose("Exiting sync on %s"%classname)

            return synced

        #
        # Synchronize foreign sites
        #

        start = time.time()

        message('Dealing with Sites')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Sites']:
            columns = peer_tables['Sites'][0].keys()
        else:
            columns = None

        # Keyed on foreign site_id
        old_peer_sites = Sites(self.api, {'peer_id': peer_id}, columns).dict('peer_site_id')
        sites_at_peer = dict([(site['site_id'], site) for site in peer_tables['Sites']])

        # Synchronize new set (still keyed on foreign site_id)
        peer_sites = sync(old_peer_sites, sites_at_peer, Site)

        for peer_site_id, site in peer_sites.iteritems():
            # Bind any newly cached sites to peer
            if peer_site_id not in old_peer_sites:
                peer.add_site(site, peer_site_id, commit = commit_mode)
                site['peer_id'] = peer_id
                site['peer_site_id'] = peer_site_id

        timers['site'] = time.time() - start

        #
        # XXX Synchronize foreign key types
        #

        message('Dealing with Keys')

        key_types = KeyTypes(self.api).dict()

        #
        # Synchronize foreign keys
        #

        start = time.time()

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Keys']:
            columns = peer_tables['Keys'][0].keys()
        else:
            columns = None

        # Keyed on foreign key_id
        old_peer_keys = Keys(self.api, {'peer_id': peer_id}, columns).dict('peer_key_id')
        keys_at_peer = dict([(key['key_id'], key) for key in peer_tables['Keys']])

        # Fix up key_type references
        for peer_key_id, key in keys_at_peer.items():
            if key['key_type'] not in key_types:
                # XXX Log an event instead of printing to logfile
                message("Warning: Skipping invalid %s key %r" % ( peer['peername'], key))
                del keys_at_peer[peer_key_id]
                continue

        # Synchronize new set (still keyed on foreign key_id)
        peer_keys = sync(old_peer_keys, keys_at_peer, Key)
        for peer_key_id, key in peer_keys.iteritems():
            # Bind any newly cached keys to peer
            if peer_key_id not in old_peer_keys:
                peer.add_key(key, peer_key_id, commit = commit_mode)
                key['peer_id'] = peer_id
                key['peer_key_id'] = peer_key_id

        timers['keys'] = time.time() - start

        #
        # Synchronize foreign users
        #

        start = time.time()

        message('Dealing with Persons')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Persons']:
            columns = peer_tables['Persons'][0].keys()
        else:
            columns = None

        # Keyed on foreign person_id
        old_peer_persons = Persons(self.api, {'peer_id': peer_id}, columns).dict('peer_person_id')

	# artificially attach the persons returned by GetPeerData to the new peer 
	# this is because validate_email needs peer_id to be correct when checking for duplicates 
	for person in peer_tables['Persons']: 
	    person['peer_id']=peer_id
        persons_at_peer = dict([(peer_person['person_id'], peer_person) \
                                for peer_person in peer_tables['Persons']])

        # XXX Do we care about membership in foreign site(s)?

        # Synchronize new set (still keyed on foreign person_id)
        peer_persons = sync(old_peer_persons, persons_at_peer, Person)

	# transcoder : retrieve a local key_id from a peer_key_id
	key_transcoder = dict ( [ (key['key_id'],peer_key_id) \
				  for peer_key_id,key in peer_keys.iteritems()])

        for peer_person_id, person in peer_persons.iteritems():
            # Bind any newly cached users to peer
            if peer_person_id not in old_peer_persons:
                peer.add_person(person, peer_person_id, commit = commit_mode)
                person['peer_id'] = peer_id
                person['peer_person_id'] = peer_person_id
                person['key_ids'] = []

            # User as viewed by peer
            peer_person = persons_at_peer[peer_person_id]
            
            # Foreign keys currently belonging to the user
	    old_person_key_ids = [key_transcoder[key_id] for key_id in person['key_ids'] \
				  if key_transcoder[key_id] in peer_keys]

            # Foreign keys that should belong to the user
	    # this is basically peer_person['key_ids'], we just check it makes sense 
	    # (e.g. we might have failed importing it)
	    person_key_ids = [ key_id for key_id in peer_person['key_ids'] if key_id in peer_keys]

            # Remove stale keys from user
	    for key_id in (set(old_person_key_ids) - set(person_key_ids)):
		person.remove_key(peer_keys[key_id], commit = commit_mode)
                message ("%s Key %d removed from person %s"%(peer['peername'], key_id, person['email']))

            # Add new keys to user
	    for key_id in (set(person_key_ids) - set(old_person_key_ids)):
		person.add_key(peer_keys[key_id], commit = commit_mode)
                message ("%s Key %d added into person %s"%(peer['peername'],key_id, person['email']))

        timers['persons'] = time.time() - start

        #
        # XXX Synchronize foreign boot states
        #

        boot_states = BootStates(self.api).dict()

        #
        # Synchronize foreign nodes
        #

        start = time.time()

        message('Dealing with Nodes (1)')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Nodes']:
            columns = peer_tables['Nodes'][0].keys()
        else:
            # smooth federation with a 4.2 peer - ignore these fields that are useless anyway
            columns = Node.fields
            if 'interface_ids' in columns: columns.remove('interface_ids')
            if 'dummybox_id' in columns: columns.remove('dummybox_id')

        # Keyed on foreign node_id
        old_peer_nodes = Nodes(self.api, {'peer_id': peer_id}, columns).dict('peer_node_id')
        nodes_at_peer = dict([(node['node_id'], node) \
                              for node in peer_tables['Nodes']])

        # Fix up site_id and boot_states references
        for peer_node_id, node in nodes_at_peer.items():
            errors = []
            if node['site_id'] not in peer_sites:
                errors.append("invalid site %d" % node['site_id'])
            if node['boot_state'] not in boot_states:
                errors.append("invalid boot state %s" % node['boot_state'])
            if errors:
                # XXX Log an event instead of printing to logfile
                message ("Warning: Skipping invalid %s node %r : " % (peer['peername'], node)\
                             + ", ".join(errors))
                del nodes_at_peer[peer_node_id]
                continue
            else:
                node['site_id'] = peer_sites[node['site_id']]['site_id']

        # Synchronize new set
        peer_nodes = sync(old_peer_nodes, nodes_at_peer, Node)

        for peer_node_id, node in peer_nodes.iteritems():
            # Bind any newly cached foreign nodes to peer
            if peer_node_id not in old_peer_nodes:
                peer.add_node(node, peer_node_id, commit = commit_mode)
                node['peer_id'] = peer_id
                node['peer_node_id'] = peer_node_id

        timers['nodes'] = time.time() - start

        #
        # Synchronize local nodes
        #

        start = time.time()
        message('Dealing with Nodes (2)')

        # Keyed on local node_id
        local_nodes = Nodes(self.api).dict()

        for node in peer_tables['PeerNodes']:
            # Foreign identifier for our node as maintained by peer
            peer_node_id = node['node_id']
            # Local identifier for our node as cached by peer
            node_id = node['peer_node_id']
            if node_id in local_nodes:
                # Still a valid local node, add it to the synchronized
                # set of local node objects keyed on foreign node_id.
                peer_nodes[peer_node_id] = local_nodes[node_id]

        timers['local_nodes'] = time.time() - start

        #
        # XXX Synchronize foreign slice instantiation states
        #

        slice_instantiations = SliceInstantiations(self.api).dict()

        #
        # Synchronize foreign slices
        #

        start = time.time()

        message('Dealing with Slices (1)')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Slices']:
            columns = peer_tables['Slices'][0].keys()
        else:
            columns = None

        # Keyed on foreign slice_id
        old_peer_slices = Slices(self.api, {'peer_id': peer_id}, columns).dict('peer_slice_id')
        slices_at_peer = dict([(slice['slice_id'], slice) \
                               for slice in peer_tables['Slices']])

        # Fix up site_id, instantiation, and creator_person_id references
        for peer_slice_id, slice in slices_at_peer.items():
            errors = []
            if slice['site_id'] not in peer_sites:
                errors.append("invalid site %d" % slice['site_id'])
            if slice['instantiation'] not in slice_instantiations:
                errors.append("invalid instantiation %s" % slice['instantiation'])
            if slice['creator_person_id'] not in peer_persons:
                # Just NULL it out
                slice['creator_person_id'] = None
            else:
                slice['creator_person_id'] = peer_persons[slice['creator_person_id']]['person_id']
            if errors:
                message("Warning: Skipping invalid %s slice %r : " % (peer['peername'], slice) \
                            + ", ".join(errors))
                del slices_at_peer[peer_slice_id]
                continue
            else:
                slice['site_id'] = peer_sites[slice['site_id']]['site_id']

        # Synchronize new set
        peer_slices = sync(old_peer_slices, slices_at_peer, Slice)

        message('Dealing with Slices (2)')
	# transcoder : retrieve a local node_id from a peer_node_id
	node_transcoder = dict ( [ (node['node_id'],peer_node_id) \
				   for peer_node_id,node in peer_nodes.iteritems()])
	person_transcoder = dict ( [ (person['person_id'],peer_person_id) \
				     for peer_person_id,person in peer_persons.iteritems()])

        for peer_slice_id, slice in peer_slices.iteritems():
            # Bind any newly cached foreign slices to peer
            if peer_slice_id not in old_peer_slices:
                peer.add_slice(slice, peer_slice_id, commit = commit_mode)
                slice['peer_id'] = peer_id
                slice['peer_slice_id'] = peer_slice_id
                slice['node_ids'] = []
                slice['person_ids'] = []

            # Slice as viewed by peer
            peer_slice = slices_at_peer[peer_slice_id]

            # Nodes that are currently part of the slice
	    old_slice_node_ids = [ node_transcoder[node_id] for node_id in slice['node_ids'] \
				   if node_id in node_transcoder and node_transcoder[node_id] in peer_nodes]

            # Nodes that should be part of the slice
	    slice_node_ids = [ node_id for node_id in peer_slice['node_ids'] if node_id in peer_nodes]

            # Remove stale nodes from slice
            for node_id in (set(old_slice_node_ids) - set(slice_node_ids)):
                slice.remove_node(peer_nodes[node_id], commit = commit_mode)
                message ("%s node %s removed from slice %s"%(peer['peername'], peer_nodes[node_id]['hostname'], slice['name']))

            # Add new nodes to slice
            for node_id in (set(slice_node_ids) - set(old_slice_node_ids)):
                slice.add_node(peer_nodes[node_id], commit = commit_mode)
                message ("%s node %s added into slice %s"%(peer['peername'], peer_nodes[node_id]['hostname'], slice['name']))

            # N.B.: Local nodes that may have been added to the slice
            # by hand, are removed. In other words, don't do this.

            # Foreign users that are currently part of the slice
	    #old_slice_person_ids = [ person_transcoder[person_id] for person_id in slice['person_ids'] \
	    #		     if person_transcoder[person_id] in peer_persons]
	    # An issue occurred with a user who registered on both sites (same email)
	    # So the remote person could not get cached locally
	    # The one-line map/filter style is nicer but ineffective here
	    old_slice_person_ids = []
	    for person_id in slice['person_ids']:
		if not person_transcoder.has_key(person_id):
                    message ('WARNING : person_id %d in %s not transcodable (1) - skipped'%(person_id,slice['name']))
		elif person_transcoder[person_id] not in peer_persons:
                    message('WARNING : person_id %d in %s not transcodable (2) - skipped'%(person_id,slice['name']))
		else:
		    old_slice_person_ids += [person_transcoder[person_id]]

            # Foreign users that should be part of the slice
	    slice_person_ids = [ person_id for person_id in peer_slice['person_ids'] if person_id in peer_persons ]

            # Remove stale users from slice
            for person_id in (set(old_slice_person_ids) - set(slice_person_ids)):
                slice.remove_person(peer_persons[person_id], commit = commit_mode)
                message ("%s user %s removed from slice %s"%(peer['peername'],peer_persons[person_id]['email'], slice['name']))

            # Add new users to slice
            for person_id in (set(slice_person_ids) - set(old_slice_person_ids)):
                slice.add_person(peer_persons[person_id], commit = commit_mode)
                message ("%s user %s added into slice %s"%(peer['peername'],peer_persons[person_id]['email'], slice['name']))

            # N.B.: Local users that may have been added to the slice
            # by hand, are not touched.

        timers['slices'] = time.time() - start

        # Update peer itself and commit
        peer.sync(commit = True)

        return timers

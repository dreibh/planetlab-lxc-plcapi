#
# Thierry Parmentelat - INRIA
# 

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
	print >>log, 'Issuing GetPeerData'
        peer_tables = peer.GetPeerData()
        timers['transport'] = time.time() - start - peer_tables['db_time']
        timers['peer_db'] = peer_tables['db_time']
        if verbose:
            print >>log, 'GetPeerData returned -> db=%d transport=%d'%(timers['peer_db'],timers['transport'])

        def sync(objects, peer_objects, classobj):
            """
            Synchronizes two dictionaries of objects. objects should
            be a dictionary of local objects keyed on their foreign
            identifiers. peer_objects should be a dictionary of
            foreign objects keyed on their local (i.e., foreign to us)
            identifiers. Returns a final dictionary of local objects
            keyed on their foreign identifiers.
            """

            if verbose:
                print >>log, 'Entering sync on',classobj(self.api).__class__.__name__

            synced = {}

            # Delete stale objects
            for peer_object_id, object in objects.iteritems():
                if peer_object_id not in peer_objects:
                    object.delete(commit = False)
                    print >> log, peer['peername'],classobj(self.api).__class__.__name__, object[object.primary_key],"deleted" 

            # Add/update new/existing objects
            for peer_object_id, peer_object in peer_objects.iteritems():
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
                    if not object.__eq__(peer_object):
                        # Only update intrinsic fields
                        object.update(object.db_fields(peer_object))
                        sync = True
                        dbg = "changed"
                    else:
                        sync = False
                        dbg = None

                    # Restore foreign identifier
                    peer_object[object.primary_key] = peer_object_id
                else:
                    # Add new object
                    object = classobj(self.api, peer_object)
                    # Replace foreign identifier with new local identifier
                    del object[object.primary_key]
                    sync = True
                    dbg = "added"

                if sync:
                    try:
                        object.sync(commit = False)
                    except PLCInvalidArgument, err:
                        # Skip if validation fails
                        # XXX Log an event instead of printing to logfile
                        print >> log, "Warning: Skipping invalid", \
                              peer['peername'], object.__class__.__name__, \
                              ":", peer_object, ":", err
                        continue

                synced[peer_object_id] = object

                if dbg:
                    print >> log, peer['peername'], classobj(self.api).__class__.__name__, object[object.primary_key], dbg

            if verbose:
                print >>log, 'Exiting sync on',classobj(self.api).__class__.__name__

            return synced

        #
        # Synchronize foreign sites
        #

        start = time.time()

	print >>log, 'Dealing with Sites'

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
                peer.add_site(site, peer_site_id, commit = False)
                site['peer_id'] = peer_id
                site['peer_site_id'] = peer_site_id

        timers['site'] = time.time() - start

        #
        # XXX Synchronize foreign key types
        #

	print >>log, 'Dealing with Keys'

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
                print >> log, "Warning: Skipping invalid %s key:" % peer['peername'], \
                      key, ": invalid key type", key['key_type']
                del keys_at_peer[peer_key_id]
                continue

        # Synchronize new set (still keyed on foreign key_id)
        peer_keys = sync(old_peer_keys, keys_at_peer, Key)
        for peer_key_id, key in peer_keys.iteritems():
            # Bind any newly cached keys to peer
            if peer_key_id not in old_peer_keys:
                peer.add_key(key, peer_key_id, commit = False)
                key['peer_id'] = peer_id
                key['peer_key_id'] = peer_key_id

        timers['keys'] = time.time() - start

        #
        # Synchronize foreign users
        #

        start = time.time()

	print >>log, 'Dealing with Persons'

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Persons']:
            columns = peer_tables['Persons'][0].keys()
        else:
            columns = None

        # Keyed on foreign person_id
        old_peer_persons = Persons(self.api, {'peer_id': peer_id}, columns).dict('peer_person_id')
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
                peer.add_person(person, peer_person_id, commit = False)
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
		person.remove_key(peer_keys[key_id], commit = False)
		print >> log, peer['peername'], 'Key', key_id, 'removed from', person['email']

            # Add new keys to user
	    for key_id in (set(person_key_ids) - set(old_person_key_ids)):
		person.add_key(peer_keys[key_id], commit = False)
		print >> log, peer['peername'], 'Key', key_id, 'added into', person['email']

        timers['persons'] = time.time() - start

        #
        # XXX Synchronize foreign boot states
        #

        boot_states = BootStates(self.api).dict()

        #
        # Synchronize foreign nodes
        #

        start = time.time()

	print >>log, 'Dealing with Nodes'

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Nodes']:
            columns = peer_tables['Nodes'][0].keys()
        else:
            columns = None

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
                print >> log, "Warning: Skipping invalid %s node:" % peer['peername'], \
                      node, ":", ", ".join(errors)
                del nodes_at_peer[peer_node_id]
                continue
            else:
                node['site_id'] = peer_sites[node['site_id']]['site_id']

        # Synchronize new set
        peer_nodes = sync(old_peer_nodes, nodes_at_peer, Node)

        for peer_node_id, node in peer_nodes.iteritems():
            # Bind any newly cached foreign nodes to peer
            if peer_node_id not in old_peer_nodes:
                peer.add_node(node, peer_node_id, commit = False)
                node['peer_id'] = peer_id
                node['peer_node_id'] = peer_node_id

        timers['nodes'] = time.time() - start

        #
        # Synchronize local nodes
        #

        start = time.time()

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

	print >>log, 'Dealing with Slices'

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
                print >> log, "Warning: Skipping invalid %s slice:" % peer['peername'], \
                      slice, ":", ", ".join(errors)
                del slices_at_peer[peer_slice_id]
                continue
            else:
                slice['site_id'] = peer_sites[slice['site_id']]['site_id']

        # Synchronize new set
        peer_slices = sync(old_peer_slices, slices_at_peer, Slice)

	# transcoder : retrieve a local node_id from a peer_node_id
	node_transcoder = dict ( [ (node['node_id'],peer_node_id) \
				   for peer_node_id,node in peer_nodes.iteritems()])
	person_transcoder = dict ( [ (person['person_id'],peer_person_id) \
				     for peer_person_id,person in peer_persons.iteritems()])

        for peer_slice_id, slice in peer_slices.iteritems():
            # Bind any newly cached foreign slices to peer
            if peer_slice_id not in old_peer_slices:
                peer.add_slice(slice, peer_slice_id, commit = False)
                slice['peer_id'] = peer_id
                slice['peer_slice_id'] = peer_slice_id
                slice['node_ids'] = []
                slice['person_ids'] = []

            # Slice as viewed by peer
            peer_slice = slices_at_peer[peer_slice_id]

            # Nodes that are currently part of the slice
	    old_slice_node_ids = [ node_transcoder[node_id] for node_id in slice['node_ids'] \
				   if node_transcoder[node_id] in peer_nodes]

            # Nodes that should be part of the slice
	    slice_node_ids = [ node_id for node_id in peer_slice['node_ids'] if node_id in peer_nodes]

            # Remove stale nodes from slice
            for node_id in (set(old_slice_node_ids) - set(slice_node_ids)):
                slice.remove_node(peer_nodes[node_id], commit = False)
		print >> log, peer['peername'], 'Node', peer_nodes[node_id]['hostname'], 'removed from', slice['name']

            # Add new nodes to slice
            for node_id in (set(slice_node_ids) - set(old_slice_node_ids)):
                slice.add_node(peer_nodes[node_id], commit = False)
		print >> log, peer['peername'], 'Node', peer_nodes[node_id]['hostname'], 'added into', slice['name']

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
		    print >> log, 'WARNING : person_id %d in %s not transcodable (1) - skipped'%(person_id,slice['name'])
		elif person_transcoder[person_id] not in peer_persons:
		    print >> log, 'WARNING : person_id %d in %s not transcodable (2) - skipped'%(person_id,slice['name'])
		else:
		    old_slice_person_ids += [person_transcoder[person_id]]

            # Foreign users that should be part of the slice
	    slice_person_ids = [ person_id for person_id in peer_slice['person_ids'] if person_id in peer_persons ]

            # Remove stale users from slice
            for person_id in (set(old_slice_person_ids) - set(slice_person_ids)):
                slice.remove_person(peer_persons[person_id], commit = False)
		print >> log, peer['peername'], 'User', peer_persons[person_id]['email'], 'removed from', slice['name']

            # Add new users to slice
            for person_id in (set(slice_person_ids) - set(old_slice_person_ids)):
                slice.add_person(peer_persons[person_id], commit = False)
		print >> log, peer['peername'], 'User', peer_persons[person_id]['email'], 'added into', slice['name']

            # N.B.: Local users that may have been added to the slice
            # by hand, are not touched.

        timers['slices'] = time.time() - start

        # Update peer itself and commit
        peer.sync(commit = True)

        return timers

#
# Thierry Parmentelat - INRIA
#
import os
import sys
import fcntl
import time

from PLC.Logger import logger
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
from PLC.Roles import Role, Roles

# settings
# initial version was doing only one final commit
# * set commit_mode to False to get that behaviour
# * set comit_mode to True to get everything synced at once
# the issue with the 'one-commit-at-the-end' approach is
# that the db gets basically totally locked during too long
# causing various issues/crashes in the rest of the system
commit_mode = True

# turn this to False only if both ends have the same db schema
# compatibility mode is a bit slower but probably safer on the long run
compatibility = True

# debugging
# for verbose output
verbose = False
use_cache = None
# for debugging specific entries - display detailed info on selected objs
focus_type = None  # set to e.g. 'Person'
# set to a list of ids (e.g. person_ids) - remote or local ids should work
focus_ids = []
# DEBUGGING SETTINGS example
# set to a filename for using cached data when debugging
# WARNING: does *not* actually connect to the peer in this case
# or more precisely, connect only if the file is not found
# i.e. the first time
# use_cache = "/var/log/peers/getpeerdata.json"
# verbose = True
# focus_type = 'Person'
# focus_ids = [621, 1088]


########## helpers

def message(to_print=None, verbose_only=False):
    if verbose_only and not verbose:
        return
    logger.info(to_print)


def message_verbose(to_print=None, header='VERBOSE'):
    message("{}> {}".format(header, to_print), verbose_only=True)


# to avoid several instances running at the same time
class FileLock:
    """
    Lock/Unlock file
    """

    def __init__(self, file_path, expire=60 * 60 * 2):
        self.expire = expire
        self.fpath = file_path
        self.fd = None

    def lock(self):
        if os.path.exists(self.fpath):
            if (time.time() - os.stat(self.fpath).st_ctime) > self.expire:
                try:
                    os.unlink(self.fpath)
                except Exception, e:
                    message('FileLock.lock({}) : {}'.format(self.fpath, e))
                    return False
        try:
            self.fd = open(self.fpath, 'w')
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError, e:
            message('FileLock.lock({}) : {}'.format(self.fpath, e))
            return False
        return True

    def unlock(self):
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN | fcntl.LOCK_NB)
            self.fd.close()
        except IOError, e:
            message('FileLock.unlock({}) : {}'.format(self.fpath, e))


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

    returns = Parameter(dict, "various timers")

    # the columns ignored in the comparison - it is safe to ignore:
    # (*) the primary key - obviously this is not expected to match
    # (*) peer_id and the transcode key, likewise
    # (*) all identifiers that refer to other objects in the db
    #     like e.g. Person.site_ids since this is managed separately
    #     and does not make sense any way
    # (*) we also ignore things like date_created and last_updated
    #     that refer to local db creation/update
    ignore_site_fields = [
        'site_id', 'peer_id', 'peer_site_id',
        'address_ids', 'node_ids', 'person_ids', 'pcu_ids', 'slice_ids', 'site_tag_ids',
        'date_created', 'last_updated',
    ]
    ignore_key_fields = [
        'key_id', 'peer_id', 'peer_key_id',
        'person_id',
    ]
    ignore_person_fields = [
        'person_id', 'peer_id', 'peer_person_id',
        'key_ids', 'slice_ids', 'person_tag_ids', 'role_ids', 'roles', 'site_ids',
        'date_created', 'last_updated',
    ]
    ignore_node_fields = [
        'node_id', 'peer_id', 'peer_node_id', 
        'node_tag_ids', 'interface_ids', 'slice_ids', 'nodegroup_ids', 'pcu_ids', 'ports',
        'date_created', 'last_updated',
        # somehow those won't print in the ple db
        'last_download', 'last_contact', 'last_pcu_reboot', 'last_boot',
        'last_time_spent_offline', 'last_time_spent_online', 'last_pcu_confirmation',
    ]
    ignore_slice_fields = [
        'slice_id', 'peer_id', 'peer_slice_id',
        'person_ids', 'slice_tag_ids', 'node_ids',
        'created',
    ]

    def call(self, auth, peer_id_or_peername):
        ret_val = None
        peername = Peers(self.api, [peer_id_or_peername], [
                         'peername'])[0]['peername']
        file_lock = FileLock("/tmp/refresh-peer-{peername}.lock"
                             .format(peername=peername))
        if not file_lock.lock():
            raise Exception, "Another instance of RefreshPeer is running."
        try:
            ret_val = self.real_call(auth, peer_id_or_peername)
        except Exception, e:
            file_lock.unlock()
            logger.exception("RefreshPeer caught exception - BEG")
            message("RefreshPeer caught exception - END")
            raise Exception, e
        file_lock.unlock()
        return ret_val

    def real_call(self, auth, peer_id_or_peername):
        # Get peer
        peers = Peers(self.api, [peer_id_or_peername])
        if not peers:
            raise PLCInvalidArgument, "No such peer '{}'".format(unicode(peer_id_or_peername))
        peer = peers[0]
        peer_id = peer['peer_id']
        peername = peer['peername']

        # Connect to peer API
        peer.connect()

        timers = {}

        # Get peer data
        start = time.time()
        message('RefreshPeer starting up (commit_mode={})'.format(commit_mode))
        if not use_cache:
            message('Issuing GetPeerData')
            peer_tables = peer.GetPeerData()
        else:
            import json
            if os.path.isfile(use_cache):
                message("use_cache: WARNING: using cached getpeerdata")
                with open(use_cache) as storage:
                    peer_tables = json.load(storage)
            else:
                message("use_cache: issuing GetPeerData")
                peer_tables = peer.GetPeerData()
                message("use_cache: saving in cache {}".format(use_cache))
                with open(use_cache, 'w') as storage:
                    json.dump(peer_tables, storage)

        # additions in June 2017

        # remove entries not marked as enabled
        # actually the 'enabled' flag is present on 'Sites' and 'Persons'
        # however we accept disabled slices as
        # (*) they don't come and go too often
        # (*) they may contain vlid nodes, that we would then lose
        #     if we were to discard those sites
        # so bottom line, we filter out only disabled persons
        for cls in ('Persons',) :
            peer_tables[cls] = [
                obj for obj in peer_tables[cls]  if obj['enabled']
            ]

        # somehow we can see GetPeerData from PLC that contains references
        # to nodes that are not exposed themselves
        # which suggests some inconsistency on their end
        # anyway, it's safer to sanitize the dataset to avoid corruption
        exposed_peer_node_ids = { n['node_id'] for n in peer_tables['Nodes']}
        for slice in peer_tables['Slices']:
            before = len(slice['node_ids'])
            slice['node_ids'] = [x for x in slice['node_ids'] if x in exposed_peer_node_ids]
            after = len(slice['node_ids'])
            if after != before:
                message("{peername} slice {slicename} got sanitized - {diff} node entries removed out of {before}"
                        .format(peername=peername, slicename=slice['name'],
                                diff=before-after, before=before))

        # end of additions

        # for smooth federation with 4.2 - ignore fields that are useless
        # anyway, and rewrite boot_state
        boot_state_rewrite = {'dbg': 'safeboot', 'diag': 'safeboot', 'disable': 'disabled',
                              'inst': 'reinstall', 'rins': 'reinstall', 'new': 'reinstall', 'rcnf': 'reinstall'}
        for node in peer_tables['Nodes']:
            for key in ['nodenetwork_ids', 'dummybox_id']:
                if key in node:
                    del node[key]
            if node['boot_state'] in boot_state_rewrite:
                node['boot_state'] = boot_state_rewrite[node['boot_state']]
        for slice in peer_tables['Slices']:
            for key in ['slice_attribute_ids']:
                if key in slice:
                    del slice[key]
        timers['transport'] = time.time() - start - peer_tables['db_time']
        timers['peer_db'] = peer_tables['db_time']
        message_verbose('GetPeerData returned -> db={} transport={}'
                        .format(timers['peer_db'], timers['transport']))

        def sync(objects, peer_objects, classobj, columns):
            """
            Synchronizes two dictionaries of objects. objects should
            be a dictionary of local objects keyed on their foreign
            identifiers. peer_objects should be a dictionary of
            foreign objects keyed on their local (i.e., foreign to us)
            identifiers. Returns a final dictionary of local objects
            keyed on their foreign identifiers.
            """

            classname = classobj(self.api).__class__.__name__
            primary_key = getattr(classobj, 'primary_key')
            # display all peer objects of these types while looping
            secondary_keys = {'Node': 'hostname', 'Slice': 'name',
                              'Person': 'email', 'Site': 'login_base'}
            secondary_key = None
            if classname in secondary_keys:
                secondary_key = secondary_keys[classname]

            message_verbose('Entering sync on {} ({})'
                            .format(classname, primary_key))

            synced = {}

            # Delete stale objects
            for peer_object_id, object in objects.iteritems():
                if peer_object_id not in peer_objects:
                    object.delete(commit=commit_mode)
                    message("{} {} {} deleted"
                            .format(peername, classname, object[primary_key]))

            total = len(peer_objects)
            count = 1

            # peer_object_id, peer_object and object are open variables in the loop below...
            # (local) object might be None if creating a new one
            def in_focus():
                if classname != focus_type:
                    return False
                return (peer_object_id in focus_ids) \
                    or (object and (primary_key in object)
                        and (object[primary_key] in focus_ids))

            def message_focus(message):
                if in_focus():
                    # always show remote
                    message_verbose("peer_obj : {} [[{}]]".format(peer_object_id, peer_object),
                                    header='FOCUS ' + message)
                    # show local object if a match was found
                    if object:
                        message_verbose("local_obj : <<{}>>".format(object),
                                        header='FOCUS ' + message)

            # the function to compare a local object with its candidate peer obj
            # xxx probably faster when compatibility is False...
            def equal_fields(object, peer_object, columns):
                # fast version: must use __eq__() instead of == since
                # peer_object may be a raw dict instead of a Peer object.
                if not compatibility:
                    result = object.__eq__(peer_object)
                    if not result:
                        message_verbose("fast mode: difference found between {} and {}"
                                        .format(object, peer_object))
                    return result
                else:
                    for column in columns:
                        if object[column] != peer_object[column]:
                            message_verbose("difference found in column {}".format(column))
                            message_verbose("our object {}".format(object[column]))
                            message_verbose("remote object {}".format(peer_object[column]))
                            return False
                    return True

            # Add/update new/existing objects
            for peer_object_id, peer_object in peer_objects.iteritems():
                peer_object_name = ""
                if secondary_key:
                    peer_object_name = "({})".format(peer_object[secondary_key])
                message_verbose('{} peer_object_id={} {} ({}/{})'
                                .format(classname, peer_object_id, peer_object_name, count, total))
                count += 1
                if peer_object_id in synced:
                    message("Warning: {peername} Skipping already added {classname}: {obj}"
                            .format(peername=peername,
                                    classname=classname, obj=peer_object))
                    continue

                if peer_object_id in objects:
                    # Update existing object
                    object = objects[peer_object_id]

                    # Replace foreign identifier with existing local
                    # identifier temporarily for the purposes of
                    # comparison.
                    peer_object[primary_key] = object[primary_key]

                    if not equal_fields(object, peer_object, columns):
                        # Only update intrinsic fields
                        object.update(object.db_fields(peer_object))
                        message_focus("DIFFERENCES : updated / syncing")
                        sync = True
                        action = "changed"
                    else:
                        message_focus("UNCHANGED - left intact / not syncing")
                        sync = False
                        action = None

                    # Restore foreign identifier
                    peer_object[primary_key] = peer_object_id
                else:
                    object = None
                    # Add new object
                    object = classobj(self.api, peer_object)
                    # Replace foreign identifier with new local identifier
                    del object[primary_key]
                    message_focus("NEW -- created with clean id - syncing")
                    sync = True
                    action = "added"

                if sync:
                    message_verbose("syncing {classname} {id} - commit_mode={mode}"
                                    .format(classname=classname,
                                            id=peer_object_id, mode=commit_mode))
                    try:
                        object.sync(commit=commit_mode)
                    except PLCInvalidArgument, err:
                        # XXX Log an event instead of printing to logfile
                        # skip if validation fails
                        message("Warning: {peername} Skipping invalid {classname} ({err})\n{object}"
                                .format(peername=peername, classname=classname,
                                        object=peer_object, err=err))
                        continue

                synced[peer_object_id] = object

                if action:
                    message("{peername}: ({count}/{total}) {classname} {primary} {name} {action}"
                            .format(peername=peername,
                                    count=count, total=total,
                                    classname=classname, primary=object[primary_key],
                                    name=peer_object_name, action=action))

            message_verbose("Exiting sync on {}".format(classname))

            return synced

        # over time, we've had issues with a given column being
        # added on one side and not on the other
        # this helper function computes the intersection of two list of
        # fields/columns
        def intersect(l1, l2):
            if compatibility:
                return list(set(l1).intersection(set(l2)))
            else:
                return l1

        # some fields definitely need to be ignored
        def ignore(l1, l2):
            return list(set(l1).difference(set(l2)))

        #
        # Synchronize foreign sites
        #

        start = time.time()

        message('(1) Dealing with Sites')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Sites']:
            columns = peer_tables['Sites'][0].keys()
            columns = intersect(columns, Site.fields)
        else:
            columns = None

        # Keyed on foreign site_id
        old_peer_sites = Sites(
            self.api, {'peer_id': peer_id}, columns).dict('peer_site_id')
        sites_at_peer = dict([(site['site_id'], site)
                              for site in peer_tables['Sites']])

        # Synchronize new set (still keyed on foreign site_id)
        peer_sites = sync(old_peer_sites, sites_at_peer, Site,
                          ignore(columns, RefreshPeer.ignore_site_fields))

        for peer_site_id, site in peer_sites.iteritems():
            # Bind any newly cached sites to peer
            if peer_site_id not in old_peer_sites:
                peer.add_site(site, peer_site_id, commit=commit_mode)
                site['peer_id'] = peer_id
                site['peer_site_id'] = peer_site_id

        timers['site'] = time.time() - start

        #
        # XXX Synchronize foreign key types
        #

        message('(2) Dealing with Keys')

        key_types = KeyTypes(self.api).dict()

        #
        # Synchronize foreign keys
        #

        start = time.time()

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Keys']:
            columns = peer_tables['Keys'][0].keys()
            columns = intersect(columns, Key.fields)
        else:
            columns = None

        # Keyed on foreign key_id
        old_peer_keys = Keys(
            self.api, {'peer_id': peer_id}, columns).dict('peer_key_id')
        keys_at_peer = dict([(key['key_id'], key)
                             for key in peer_tables['Keys']])

        # Fix up key_type references
        for peer_key_id, key in keys_at_peer.items():
            if key['key_type'] not in key_types:
                # XXX Log an event instead of printing to logfile
                message("Warning: Skipping invalid {peername} key {key}"
                        .format(peername=peername, key=key))
                del keys_at_peer[peer_key_id]
                continue

        # Synchronize new set (still keyed on foreign key_id)
        peer_keys = sync(old_peer_keys, keys_at_peer, Key,
                         ignore(columns, RefreshPeer.ignore_key_fields))
        for peer_key_id, key in peer_keys.iteritems():
            # Bind any newly cached keys to peer
            if peer_key_id not in old_peer_keys:
                peer.add_key(key, peer_key_id, commit=commit_mode)
                key['peer_id'] = peer_id
                key['peer_key_id'] = peer_key_id

        timers['keys'] = time.time() - start

        #
        # Synchronize foreign users
        #

        start = time.time()

        message('(3) Dealing with Persons')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Persons']:
            columns = peer_tables['Persons'][0].keys()
            columns = intersect(columns, Person.fields)
        else:
            columns = None

        # Keyed on foreign person_id
        old_peer_persons = Persons(
            self.api, {'peer_id': peer_id}, columns).dict('peer_person_id')

        # artificially attach the persons returned by GetPeerData to the new peer
        # this is because validate_email needs peer_id to be correct when
        # checking for duplicates
        for person in peer_tables['Persons']:
            person['peer_id'] = peer_id
        persons_at_peer = dict([(peer_person['person_id'], peer_person)
                                for peer_person in peer_tables['Persons']])

        # XXX Do we care about membership in foreign site(s)?

        # Synchronize new set (still keyed on foreign person_id)
        peer_persons = sync(old_peer_persons, persons_at_peer, Person,
                            ignore(columns, RefreshPeer.ignore_person_fields))

        # transcoder : retrieve a local key_id from a peer_key_id
        key_transcoder = dict([(key['key_id'], peer_key_id)
                               for peer_key_id, key in peer_keys.iteritems()])

        for peer_person_id, person in peer_persons.iteritems():
            # Bind any newly cached users to peer
            if peer_person_id not in old_peer_persons:
                peer.add_person(person, peer_person_id, commit=commit_mode)
                person['peer_id'] = peer_id
                person['peer_person_id'] = peer_person_id
                person['key_ids'] = []

            # User as viewed by peer
            peer_person = persons_at_peer[peer_person_id]

            # Foreign keys currently belonging to the user
            old_person_key_ids = [key_transcoder[key_id] for key_id in person['key_ids']
                                  if key_transcoder[key_id] in peer_keys]

            # Foreign keys that should belong to the user
            # this is basically peer_person['key_ids'], we just check it makes sense
            # (e.g. we might have failed importing it)
            person_key_ids = [key_id for key_id in peer_person[
                'key_ids'] if key_id in peer_keys]

            # Remove stale keys from user
            for key_id in (set(old_person_key_ids) - set(person_key_ids)):
                person.remove_key(peer_keys[key_id], commit=commit_mode)
                message("{peername} Key {key_id} removed from person {email}"
                        .format(peername=peername,
                                key_id=key_id, email=person['email']))

            # Add new keys to user
            for key_id in (set(person_key_ids) - set(old_person_key_ids)):
                #message("before add_key, passing person={}".format(person))
                #message("before add_key, passing key={}".format(peer_keys[key_id]))
                person.add_key(peer_keys[key_id], commit=commit_mode)
                message("{} Key {} added into person {}"
                        .format(peername, key_id, person['email']))

        timers['persons'] = time.time() - start

        #
        # XXX Synchronize foreign boot states
        #

        boot_states = BootStates(self.api).dict()

        #
        # Synchronize foreign nodes
        #

        start = time.time()

        # NOTE: we do import disabled sites
        message('(4) Dealing with Nodes (1)')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Nodes']:
            columns = peer_tables['Nodes'][0].keys()
            columns = intersect(columns, Node.fields)
        else:
            columns = Node.fields

        # Keyed on foreign node_id
        old_peer_nodes = Nodes(
            self.api, {'peer_id': peer_id}, columns).dict('peer_node_id')
        nodes_at_peer = dict([(node['node_id'], node)
                              for node in peer_tables['Nodes']])

        # Fix up site_id and boot_states references
        for peer_node_id, node in nodes_at_peer.items():
            errors = []
            if node['site_id'] not in peer_sites:
                errors.append("invalid (or disabled) site {}".format(node['site_id']))
            if node['boot_state'] not in boot_states:
                errors.append("invalid boot state {}".format(node['boot_state']))
            if errors:
                # XXX Log an event instead of printing to logfile
                message("Warning: Skipping invalid {peername} node {hostname} - {errors}"
                        .format(peername=peername,
                                hostname=node['hostname'], errors=", ".join(errors)))
                del nodes_at_peer[peer_node_id]
                continue
            else:
                node['site_id'] = peer_sites[node['site_id']]['site_id']

        # Synchronize new set
        peer_nodes = sync(old_peer_nodes, nodes_at_peer, Node,
                          ignore(columns, RefreshPeer.ignore_node_fields))

        for peer_node_id, node in peer_nodes.iteritems():
            # Bind any newly cached foreign nodes to peer
            if peer_node_id not in old_peer_nodes:
                peer.add_node(node, peer_node_id, commit=commit_mode)
                node['peer_id'] = peer_id
                node['peer_node_id'] = peer_node_id

        timers['nodes'] = time.time() - start

        #
        # Synchronize local nodes
        #

        start = time.time()
        message('(5) Dealing with Nodes (2)')

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

        message('(6) Dealing with Slices')

        # Compare only the columns returned by the GetPeerData() call
        if peer_tables['Slices']:
            columns = peer_tables['Slices'][0].keys()
            columns = intersect(columns, Slice.fields)
        else:
            columns = None

        # Keyed on foreign slice_id
        old_peer_slices = Slices(
            self.api, {'peer_id': peer_id}, columns).dict('peer_slice_id')
        slices_at_peer = dict([(slice['slice_id'], slice)
                               for slice in peer_tables['Slices']])

        # Fix up site_id, instantiation, and creator_person_id references
        for peer_slice_id, slice in slices_at_peer.items():
            errors = []
            if slice['site_id'] not in peer_sites:
                errors.append("invalid site {}".format(slice['site_id']))
            if slice['instantiation'] not in slice_instantiations:
                errors.append("invalid instantiation {}"
                              .format(slice['instantiation']))
            if slice['creator_person_id'] not in peer_persons:
                # Just NULL it out
                slice['creator_person_id'] = None
            else:
                slice['creator_person_id'] = peer_persons[
                    slice['creator_person_id']]['person_id']
            if errors:
                message("Warning: Skipping invalid {peername} slice {slice} : {errors}"
                        .format(peername=peername,
                                slice=slice, errors=", ".join(errors)))
                del slices_at_peer[peer_slice_id]
                continue
            else:
                slice['site_id'] = peer_sites[slice['site_id']]['site_id']

        # Synchronize new set 
        peer_slices = sync(old_peer_slices, slices_at_peer, Slice,
                           ignore(columns, RefreshPeer.ignore_slice_fields))

        message('(7) Dealing with Nodes in Slices')
        # transcoder : retrieve a local node_id from a peer_node_id
        node_transcoder = dict([(node['node_id'], peer_node_id)
                                for peer_node_id, node in peer_nodes.iteritems()])
        person_transcoder = dict([(person['person_id'], peer_person_id)
                                  for peer_person_id, person in peer_persons.iteritems()])

        for peer_slice_id, slice in peer_slices.iteritems():
            # Bind any newly cached foreign slices to peer
            if peer_slice_id not in old_peer_slices:
                peer.add_slice(slice, peer_slice_id, commit=commit_mode)
                slice['peer_id'] = peer_id
                slice['peer_slice_id'] = peer_slice_id
                slice['node_ids'] = []
                slice['person_ids'] = []

            # Slice as viewed by peer
            peer_slice = slices_at_peer[peer_slice_id]

            # Nodes that are currently part of the slice
            old_slice_node_ids = [node_transcoder[node_id] for node_id in slice['node_ids']
                                  if node_id in node_transcoder and node_transcoder[node_id] in peer_nodes]

            # Nodes that should be part of the slice
            slice_node_ids = [node_id for node_id in peer_slice['node_ids']
                              if node_id in peer_nodes]

            # Remove stale nodes from slice
            for node_id in (set(old_slice_node_ids) - set(slice_node_ids)):
                slice.remove_node(peer_nodes[node_id], commit=commit_mode)
                message("{peername} node {hostname} (id {node_id}) removed from slice {slicename} (id {slice_id})"
                        .format(peername=peername,
                                hostname=peer_nodes[node_id]['hostname'], node_id=peer_nodes[node_id]['node_id'],
                                slicename=slice['name'], slice_id=slice['slice_id']))

            # Add new nodes to slice
            for node_id in (set(slice_node_ids) - set(old_slice_node_ids)):
                slice.add_node(peer_nodes[node_id], commit=commit_mode)
                message("{peername} node {hostname} (id {node_id}) added into slice {slicename} (id {slice_id})"
                        .format(peername=peername,
                                hostname=peer_nodes[node_id]['hostname'], node_id=peer_nodes[node_id]['node_id'],
                                slicename=slice['name'], slice_id=slice['slice_id']))

            if slice['slice_id'] == 225:
                return

            # N.B.: Local nodes that may have been added to the slice
            # by hand, are removed. In other words, don't do this.

            # Foreign users that are currently part of the slice
            # old_slice_person_ids = [ person_transcoder[person_id] for person_id in slice['person_ids'] \
            #                if person_transcoder[person_id] in peer_persons]
            # An issue occurred with a user who registered on both sites (same email)
            # So the remote person could not get cached locally
            # The one-line map/filter style is nicer but ineffective here
            old_slice_person_ids = []
            for person_id in slice['person_ids']:
                if not person_transcoder.has_key(person_id):
                    message('WARNING : person_id {person_id} in {slicename} not transcodable (1) - skipped'
                            .format(person_id=person_id, slicename=slice['name']))
                elif person_transcoder[person_id] not in peer_persons:
                    message('WARNING : person_id {person_id} in {slicename} not transcodable (2) - skipped'
                            .format(person_id=person_id, slicename=slice['name']))
                else:
                    old_slice_person_ids += [person_transcoder[person_id]]

            # Foreign users that should be part of the slice
            slice_person_ids = [person_id for person_id in peer_slice[
                'person_ids'] if person_id in peer_persons]

            # Remove stale users from slice
            for person_id in (set(old_slice_person_ids) - set(slice_person_ids)):
                slice.remove_person(
                    peer_persons[person_id], commit=commit_mode)
                message("{peername} user {email} removed from slice {slicename}"
                        .format(peername=peername,
                                email=peer_persons[person_id]['email'],
                                slicename=slice['name']))

            # Add new users to slice
            for person_id in (set(slice_person_ids) - set(old_slice_person_ids)):
                slice.add_person(peer_persons[person_id], commit=commit_mode)
                message("{peername} user {email} added into slice {slicename}"
                        .format(peername=peername,
                                email=peer_persons[person_id]['email'],
                                slicename=slice['name']))

            # N.B.: Local users that may have been added to the slice
            # by hand, are not touched.

        timers['slices'] = time.time() - start

        #
        # Persons x Sites
        #
        start = time.time()

        message('(8) Dealing with Persons in Sites')

        for peer_site_id, site in peer_sites.iteritems():
            # Site as viewed by peer
            peer_site = sites_at_peer[peer_site_id]

            # Persons that are currently part of the site
            old_site_person_ids = [person_transcoder[person_id] for person_id in site['person_ids']
                                   if person_id in person_transcoder and person_transcoder[person_id] in peer_persons]

            # Perons that should be part of the site
            site_person_ids = [person_id for person_id in peer_site[
                'person_ids'] if person_id in peer_persons]

            # Remove stale persons from site
            for person_id in (set(old_site_person_ids) - set(site_person_ids)):
                site.remove_person(peer_persons[person_id], commit=commit_mode)
                message("{peername} person {email} removed from site {login_base}"
                        .format(peername=peername,
                                email=peer_persons[person_id]['email'],
                                login_base=site['login_base']))

            # Add new persons to site
            for person_id in (set(site_person_ids) - set(old_site_person_ids)):
                site.add_person(peer_persons[person_id], commit=commit_mode)
                message("{peername} person {email} added into site {login_base}"
                        .format(peername=peername,
                                email=peer_persons[person_id]['email'],
                                login_base=site['login_base']))

        timers['sites-persons'] = time.time() - start

        #
        # Persons x Roles
        #
        start = time.time()

        message('(9) Dealing with Roles for Persons')

        roles = Roles(self.api)
        roles_dict = dict([(role['role_id'], role) for role in roles])
        for peer_person_id, person in peer_persons.iteritems():
            # Person as viewed by peer
            peer_person = persons_at_peer[peer_person_id]

            # Roles that are currently attributed for the person
            old_person_role_ids = [role_id for role_id in person['role_ids']]

            # Roles that should be attributed to the person
            person_role_ids = [role_id for role_id in peer_person['role_ids']]

            # Remove stale roles
            for role_id in (set(old_person_role_ids) - set(person_role_ids)):
                person.remove_role(roles_dict[role_id], commit=commit_mode)
                message("{peername} role {rolename} removed from person {email}"
                        .format(peername=peername,
                                rolename=roles_dict[role_id]['name'],
                                email=person['email']))

            # Add new roles to person
            for role_id in (set(person_role_ids) - set(old_person_role_ids)):
                person.add_role(roles_dict[role_id], commit=commit_mode)
                message("{peername} role {rolename} added from person {email}"
                        .format(peername=peername,
                                rolename=roles_dict[role_id]['name'],
                                email=person['email']))

        timers['persons-roles'] = time.time() - start

        # Update peer itself and commit
        peer.sync(commit=True)

        return timers

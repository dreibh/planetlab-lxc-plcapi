import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Slices import Slice, Slices
from PLC.Persons import Person, Persons
from PLC.Sites import Sites
from PLC.Roles import Roles
from PLC.Keys import Key, Keys
from PLC.SliceTags import SliceTag, SliceTags
from PLC.InitScripts import InitScript, InitScripts
from PLC.Leases import Lease, Leases
from PLC.Timestamp import Duration
from PLC.Methods.GetSliceFamily import GetSliceFamily
from PLC.PersonTags import PersonTag,PersonTags

from PLC.Accessors.Accessors_standard import *

# XXX used to check if slice expiration time is sane
MAXINT =  2L**31-1

# slice_filter essentially contains the slice_ids for the relevant slices (on the node + system & delegated slices)
def get_slivers(api, caller, auth, slice_filter, node = None):
    # Get slice information
    slices = Slices(api, slice_filter, ['slice_id', 'name', 'instantiation', 'expires', 'person_ids', 'slice_tag_ids'])

    # Build up list of users and slice attributes
    person_ids = set()
    slice_tag_ids = set()
    for slice in slices:
        person_ids.update(slice['person_ids'])
        slice_tag_ids.update(slice['slice_tag_ids'])

    # Get user information
    all_persons = Persons(api, {'person_id':person_ids,'enabled':True}, ['person_id', 'enabled', 'key_ids']).dict()

    # Build up list of keys
    key_ids = set()
    for person in all_persons.values():
        key_ids.update(person['key_ids'])

    # Get user account keys
    all_keys = Keys(api, key_ids, ['key_id', 'key', 'key_type']).dict()

    # Get slice attributes
    all_slice_tags = SliceTags(api, slice_tag_ids).dict()

    slivers = []
    for slice in slices:
        keys = []
        for person_id in slice['person_ids']:
            if person_id in all_persons:
                person = all_persons[person_id]
                if not person['enabled']:
                    continue
                for key_id in person['key_ids']:
                    if key_id in all_keys:
                        key = all_keys[key_id]
                        keys += [{'key_type': key['key_type'],
                                  'key': key['key']}]

        attributes = []

        # All (per-node and global) attributes for this slice
        slice_tags = []
        for slice_tag_id in slice['slice_tag_ids']:
            if slice_tag_id in all_slice_tags:
                slice_tags.append(all_slice_tags[slice_tag_id])

        # Per-node sliver attributes take precedence over global
        # slice attributes, so set them first.
        # Then comes nodegroup slice attributes
        # Followed by global slice attributes
        sliver_attributes = []

        if node is not None:
            for sliver_attribute in [ a for a in slice_tags if a['node_id'] == node['node_id'] ]:
                sliver_attributes.append(sliver_attribute['tagname'])
                attributes.append({'tagname': sliver_attribute['tagname'],
                                   'value': sliver_attribute['value']})

            # set nodegroup slice attributes
            for slice_tag in [ a for a in slice_tags if a['nodegroup_id'] in node['nodegroup_ids'] ]:
                # Do not set any nodegroup slice attributes for
                # which there is at least one sliver attribute
                # already set.
                if slice_tag['tagname'] not in sliver_attributes:
                    sliver_attributes.append(slice_tag['tagname'])
                    attributes.append({'tagname': slice_tag['tagname'],
                                       'value': slice_tag['value']})

        for slice_tag in [ a for a in slice_tags if a['node_id'] is None and a['nodegroup_id'] is None ]:
            # Do not set any global slice attributes for
            # which there is at least one sliver attribute
            # already set.
            if slice_tag['tagname'] not in sliver_attributes:
                attributes.append({'tagname': slice_tag['tagname'],
                                   'value': slice_tag['value']})

        # XXX Sanity check; though technically this should be a system invariant
        # checked with an assertion
        if slice['expires'] > MAXINT:  slice['expires']= MAXINT

        # expose the slice vref as computed by GetSliceFamily
        family = GetSliceFamily (api,caller).call(auth, slice['slice_id'])

        slivers.append({
            'name': slice['name'],
            'slice_id': slice['slice_id'],
            'instantiation': slice['instantiation'],
            'expires': slice['expires'],
            'keys': keys,
            'attributes': attributes,
            'GetSliceFamily': family,
            })

    return slivers

### The pickle module, used in conjunction with caching has a restriction that it does not
### work on "connection objects." It doesn't matter if the connection object has
### an 'str' or 'repr' method, there is a taint check that throws an exception if
### the pickled class is found to derive from a connection.
### (To be moved to Method.py)

def sanitize_for_pickle (obj):
    if (isinstance(obj, dict)):
        parent = dict(obj)
        for k in parent.keys(): parent[k] = sanitize_for_pickle (parent[k])
        return parent
    elif (isinstance(obj, list)):
        parent = list(obj)
        parent = map(sanitize_for_pickle, parent)
        return parent
    else:
        return obj

class GetSlivers(Method):
    """
    Returns a struct containing information about the specified node
    (or calling node, if called by a node and node_id_or_hostname is
    not specified), including the current set of slivers bound to the
    node.

    All of the information returned by this call can be gathered from
    other calls, e.g. GetNodes, GetInterfaces, GetSlices, etc. This
    function exists almost solely for the benefit of Node Manager.
    """

    roles = ['admin', 'node']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        ]

    returns = {
        'timestamp': Parameter(int, "Timestamp of this call, in seconds since UNIX epoch"),
        'node_id': Node.fields['node_id'],
        'hostname': Node.fields['hostname'],
        'interfaces': [Interface.fields],
        'groups': [NodeGroup.fields['groupname']],
        'conf_files': [ConfFile.fields],
        'initscripts': [InitScript.fields],
        'accounts': [{
            'name': Parameter(str, "unix style account name", max = 254),
            'keys': [{
                'key_type': Key.fields['key_type'],
                'key': Key.fields['key']
            }],
            }],
        'slivers': [{
            'name': Slice.fields['name'],
            'slice_id': Slice.fields['slice_id'],
            'instantiation': Slice.fields['instantiation'],
            'expires': Slice.fields['expires'],
            'keys': [{
                'key_type': Key.fields['key_type'],
                'key': Key.fields['key']
            }],
            'attributes': [{
                'tagname': SliceTag.fields['tagname'],
                'value': SliceTag.fields['value']
            }]
        }],
        # how to reach the xmpp server
        'xmpp': {'server':Parameter(str,"hostname for the XMPP server"),
                 'user':Parameter(str,"username for the XMPP server"),
                 'password':Parameter(str,"username for the XMPP server"),
                 },
        # we consider three policies (reservation-policy)
        # none : the traditional way to use a node
        # lease_or_idle : 0 or 1 slice runs at a given time
        # lease_or_shared : 1 slice is running during a lease, otherwise all the slices come back
        'reservation_policy': Parameter(str,"one among none, lease_or_idle, lease_or_shared"),
        'leases': [  { 'slice_id' : Lease.fields['slice_id'],
                       't_from' : Lease.fields['t_from'],
                       't_until' : Lease.fields['t_until'],
                       }],
    }

    def call(self, auth, node_id_or_hostname = None):
        return self.raw_call(auth, node_id_or_hostname)


    def raw_call(self, auth, node_id_or_hostname):
        timestamp = int(time.time())

        # Get node
        if node_id_or_hostname is None:
            if isinstance(self.caller, Node):
                node = self.caller
            else:
                raise PLCInvalidArgument, "'node_id_or_hostname' not specified"
        else:
            nodes = Nodes(self.api, [node_id_or_hostname])
            if not nodes:
                raise PLCInvalidArgument, "No such node"
            node = nodes[0]

            if node['peer_id'] is not None:
                raise PLCInvalidArgument, "Not a local node"

        # Get interface information
        interfaces = Interfaces(self.api, node['interface_ids'])

        # Get node group information
        nodegroups = NodeGroups(self.api, node['nodegroup_ids']).dict('groupname')
        groups = nodegroups.keys()

        # Get all (enabled) configuration files
        all_conf_files = ConfFiles(self.api, {'enabled': True}).dict()
        conf_files = {}

        # Global configuration files are the default. If multiple
        # entries for the same global configuration file exist, it is
        # undefined which one takes precedence.
        for conf_file in all_conf_files.values():
            if not conf_file['node_ids'] and not conf_file['nodegroup_ids']:
                conf_files[conf_file['dest']] = conf_file

        # Node group configuration files take precedence over global
        # ones. If a node belongs to multiple node groups for which
        # the same configuration file is defined, it is undefined
        # which one takes precedence.
        for nodegroup in nodegroups.values():
            for conf_file_id in nodegroup['conf_file_ids']:
                if conf_file_id in all_conf_files:
                    conf_file = all_conf_files[conf_file_id]
                    conf_files[conf_file['dest']] = conf_file

        # Node configuration files take precedence over node group
        # configuration files.
        for conf_file_id in node['conf_file_ids']:
            if conf_file_id in all_conf_files:
                conf_file = all_conf_files[conf_file_id]
                conf_files[conf_file['dest']] = conf_file

        # Get all (enabled) initscripts
        initscripts = InitScripts(self.api, {'enabled': True})

        # Get system slices
        system_slice_tags = SliceTags(self.api, {'tagname': 'system', 'value': '1'}).dict('slice_id')
        system_slice_ids = system_slice_tags.keys()

        # Get nm-controller slices
        # xxx Thierry: should these really be exposed regardless of their mapping to nodes ?
        controller_and_delegated_slices = Slices(self.api, {'instantiation': ['nm-controller', 'delegated']}, ['slice_id']).dict('slice_id')
        controller_and_delegated_slice_ids = controller_and_delegated_slices.keys()
        slice_ids = system_slice_ids + controller_and_delegated_slice_ids + node['slice_ids']

        slivers = get_slivers(self.api, self.caller, auth, slice_ids, node)

        # get the special accounts and keys needed for the node
        # root
        # site_admin
        accounts = []
        if False and 'site_id' not in node:
            nodes = Nodes(self.api, node['node_id'])
            node = nodes[0]

        # used in conjunction with reduce to flatten lists, like in
        # reduce ( reduce_flatten_list, [ [1] , [2,3] ], []) => [ 1,2,3 ]
        def reduce_flatten_list (x,y): return x+y

        # root users are users marked with the tag 'isrootonsite'. Hack for Mlab and other sites in which admins participate in diagnosing problems.
        def get_site_root_user_keys(api,site_id_or_name):
           site = Sites (api,site_id_or_name,['person_ids'])[0]
           all_site_persons = site['person_ids']
           all_site_person_tags = PersonTags(self.api,{'person_id':all_site_persons,'tagname':'isrootonsite'},['value','person_id'])
           site_root_person_tags = filter(lambda r:r['value']=='true',all_site_person_tags)
           site_root_person_ids = map(lambda r:r['person_id'],site_root_person_tags)
           key_ids = reduce (reduce_flatten_list,
                             [ p['key_ids'] for p in \
                                   Persons(api,{ 'person_id':site_root_person_ids,
                                                 'enabled':True, '|role_ids' : [20, 40] },
                                           ['key_ids']) ],
                             [])
           return [ key['key'] for key in Keys (api, key_ids) if key['key_type']=='ssh']

        # power users are pis and techs
        def get_site_power_user_keys(api,site_id_or_name):
            site = Sites (api,site_id_or_name,['person_ids'])[0]
            key_ids = reduce (reduce_flatten_list,
                              [ p['key_ids'] for p in \
                                    Persons(api,{ 'person_id':site['person_ids'],
                                                  'enabled':True, '|role_ids' : [20, 40] },
                                            ['key_ids']) ],
                              [])
            return [ key['key'] for key in Keys (api, key_ids) if key['key_type']=='ssh']

        # all admins regardless of their site
        def get_all_admin_keys(api):
            key_ids = reduce (reduce_flatten_list,
                              [ p['key_ids'] for p in \
                                    Persons(api, {'peer_id':None, 'enabled':True, '|role_ids':[10] },
                                            ['key_ids']) ],
                              [])
            return [ key['key'] for key in Keys (api, key_ids) if key['key_type']=='ssh']

        # 'site_admin' account setup
        personsitekeys=get_site_power_user_keys(self.api,node['site_id'])
        accounts.append({'name':'site_admin','keys':personsitekeys})

        # 'root' account setup on nodes from all 'admin' users and ones marked with 'isrootonsite' for this site
        siterootkeys=get_site_root_user_keys(self.api,node['site_id'])
        personsitekeys=get_all_admin_keys(self.api)
        personsitekeys.extend(siterootkeys)

        accounts.append({'name':'root','keys':personsitekeys})

        hrn = GetNodeHrn(self.api,self.caller).call(auth,node['node_id'])

        # XMPP config for omf federation
        try:
            if not self.api.config.PLC_OMF_ENABLED:
                raise Exception,"OMF not enabled"
            xmpp={'server':self.api.config.PLC_OMF_XMPP_SERVER}
        except:
            xmpp={'server':None}

        node.update_last_contact()

        # expose leases & reservation policy
        # in a first implementation we only support none and lease_or_idle
        lease_exposed_fields = [ 'slice_id', 't_from', 't_until', 'name', ]
        leases=None
        if node['node_type'] != 'reservable':
            reservation_policy='none'
        else:
            reservation_policy='lease_or_idle'
            # expose the leases for the next 24 hours
            leases = [ dict ( [ (k,l[k]) for k in lease_exposed_fields ] )
                       for l in Leases (self.api, {'node_id':node['node_id'],
                                                   'clip': (timestamp, timestamp+24*Duration.HOUR),
                                                   '-SORT': 't_from',
                                                   }) ]
        granularity=self.api.config.PLC_RESERVATION_GRANULARITY

        raw_data = {
            'timestamp': timestamp,
            'node_id': node['node_id'],
            'hostname': node['hostname'],
            'interfaces': interfaces,
            'groups': groups,
            'conf_files': conf_files.values(),
            'initscripts': initscripts,
            'slivers': slivers,
            'accounts': accounts,
            'xmpp':xmpp,
            'hrn':hrn,
            'reservation_policy': reservation_policy,
            'leases':leases,
            'lease_granularity': granularity,
        }

        sanitized_data = sanitize_for_pickle (raw_data)
        return sanitized_data


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
from PLC.Keys import Key, Keys
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.InitScripts import InitScript, InitScripts

def get_slivers(api, slice_filter, node = None):
    # Get slice information
    slices = Slices(api, slice_filter, ['slice_id', 'name', 'instantiation', 'expires', 'person_ids', 'slice_attribute_ids'])

    # Build up list of users and slice attributes
    person_ids = set()
    slice_attribute_ids = set()
    for slice in slices:
        person_ids.update(slice['person_ids'])
        slice_attribute_ids.update(slice['slice_attribute_ids'])

    # Get user information
    all_persons = Persons(api, {'person_id':person_ids,'enabled':True}, ['person_id', 'enabled', 'key_ids']).dict()

    # Build up list of keys
    key_ids = set()
    for person in all_persons.values():
        key_ids.update(person['key_ids'])

    # Get user account keys
    all_keys = Keys(api, key_ids, ['key_id', 'key', 'key_type']).dict()

    # Get slice attributes
    all_slice_attributes = SliceAttributes(api, slice_attribute_ids).dict()

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
        slice_attributes = []
        for slice_attribute_id in slice['slice_attribute_ids']:
            if slice_attribute_id in all_slice_attributes:
                slice_attributes.append(all_slice_attributes[slice_attribute_id])

        # Per-node sliver attributes take precedence over global
        # slice attributes, so set them first.
        # Then comes nodegroup slice attributes
	# Followed by global slice attributes
        sliver_attributes = []

        if node is not None:
            for sliver_attribute in filter(lambda a: a['node_id'] == node['node_id'], slice_attributes):
                sliver_attributes.append(sliver_attribute['tagname'])
                attributes.append({'tagname': sliver_attribute['tagname'],
                                   'value': sliver_attribute['value']})

	    # set nodegroup slice attributes
	    for slice_attribute in filter(lambda a: a['nodegroup_id'] in node['nodegroup_ids'], slice_attributes):
	        # Do not set any nodegroup slice attributes for
                # which there is at least one sliver attribute
                # already set.
	        if slice_attribute['tagname'] not in slice_attributes:
		    attributes.append({'tagname': slice_attribute['tagname'],
				   'value': slice_attribute['value']})

        for slice_attribute in filter(lambda a: a['node_id'] is None, slice_attributes):
            # Do not set any global slice attributes for
            # which there is at least one sliver attribute
            # already set.
            if slice_attribute['tagname'] not in sliver_attributes:
                attributes.append({'tagname': slice_attribute['tagname'],
                                   'value': slice_attribute['value']})

        slivers.append({
            'name': slice['name'],
            'slice_id': slice['slice_id'],
            'instantiation': slice['instantiation'],
            'expires': slice['expires'],
            'keys': keys,
            'attributes': attributes
            })

    return slivers

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
        'networks': [Interface.fields],
        'groups': [NodeGroup.fields['groupname']],
        'conf_files': [ConfFile.fields],
	'initscripts': [InitScript.fields],
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
                'tagname': SliceAttribute.fields['tagname'],
                'value': SliceAttribute.fields['value']
            }]
        }]
    }

    def call(self, auth, node_id_or_hostname = None):
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
        networks = Interfaces(self.api, node['interface_ids'])

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
        system_slice_attributes = SliceAttributes(self.api, {'tagname': 'system', 'value': '1'}).dict('slice_id')
        system_slice_ids = system_slice_attributes.keys()
	
	# Get nm-controller slices
	controller_and_delegated_slices = Slices(self.api, {'instantiation': ['nm-controller', 'delegated']}, ['slice_id']).dict('slice_id')
	controller_and_delegated_slice_ids = controller_and_delegated_slices.keys()
	slice_ids = system_slice_ids + controller_and_delegated_slice_ids + node['slice_ids']

	slivers = get_slivers(self.api, slice_ids, node)

	node.update_last_contact()

        return {
            'timestamp': timestamp,
            'node_id': node['node_id'],
            'hostname': node['hostname'],
            'networks': networks,
            'groups': groups,
            'conf_files': conf_files.values(),
	    'initscripts': initscripts,
            'slivers': slivers
            }

import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Slices import Slice, Slices
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.SliceAttributes import SliceAttribute, SliceAttributes

def hashref(rows, key_field):
    d = {}
    for row in rows:
        d[row[key_field]] = row
    return d

class GetSlivers(Method):
    """
    Returns an array of structs representing nodes and their slivers
    (slices bound to nodes). If node_filter is specified, only
    information about the specified nodes will be returned. If
    node_filter is not specified and called by a node, only
    information about the caller will be returned.

    All of the information returned by this call can be gathered from
    other calls, e.g. GetNodes, GetNodeNetworks, GetSlices, etc. This
    function exists primarily for the benefit of Node Manager and
    Federation Manager.
    """

    roles = ['admin', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(Node.fields['node_id'],
                     Node.fields['hostname'])],
              Filter(Node.fields)),
        ]

    returns = [{
        'timestamp': Parameter(int, "Timestamp of this call, in seconds since UNIX epoch"),
        'node_id': Node.fields['node_id'],
        'hostname': Node.fields['hostname'],
        'networks': [NodeNetwork.fields],
        'groups': [NodeGroup.fields['name']],
        'conf_files': [ConfFile.fields],
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
                'name': SliceAttribute.fields['name'],
                'value': SliceAttribute.fields['value']
            }]
        }]
    }]

    def call(self, auth, node_filter = None):
        timestamp = int(time.time())

        if node_filter is None and isinstance(self.caller, Node):
            all_nodes = {self.caller['node_id']: self.caller}
        else:
            all_nodes = hashref(Nodes(self.api, node_filter), 'node_id')
            # XXX Add foreign nodes

        nodenetwork_ids = set()
        nodegroup_ids = set()
        slice_ids = set()
        for node_id, node in all_nodes.iteritems():
            nodenetwork_ids.update(node['nodenetwork_ids'])
            nodegroup_ids.update(node['nodegroup_ids'])
            slice_ids.update(node['slice_ids'])

        # Get nodenetwork information
        all_nodenetworks = hashref(NodeNetworks(self.api, nodenetwork_ids), 'nodenetwork_id')

        # Get node group information
        all_nodegroups = hashref(NodeGroups(self.api, nodegroup_ids), 'nodegroup_id')

        # Get (enabled) configuration files
        all_conf_files = hashref(ConfFiles(self.api, {'enabled': True}), 'conf_file_id')

        if slice_ids:
            # Get slices
            all_slices = hashref(Slices(self.api, slice_ids), 'slice_id')

            person_ids = set()
            slice_attribute_ids = set()
            for slice_id, slice in all_slices.iteritems():
                person_ids.update(slice['person_ids'])
                slice_attribute_ids.update(slice['slice_attribute_ids'])

            # Get user accounts
            all_persons = hashref(Persons(self.api, person_ids), 'person_id')

            key_ids = set()
            for person_id, person in all_persons.iteritems():
                key_ids.update(person['key_ids'])

            # Get user account keys
            all_keys = hashref(Keys(self.api, key_ids), 'key_id')

            # Get slice attributes
            all_slice_attributes = hashref(SliceAttributes(self.api, slice_attribute_ids), 'slice_attribute_id')

        nodes = []
        for node_id, node in all_nodes.iteritems():
            networks = [all_nodenetworks[nodenetwork_id] for nodenetwork_id in node['nodenetwork_ids']]
            nodegroups = [all_nodegroups[nodegroup_id] for nodegroup_id in node['nodegroup_ids']]
            groups = [nodegroup['name'] for nodegroup in nodegroups]

            # If multiple entries for the same global configuration
            # file exist, it is undefined which one takes precedence.
            conf_files = {}
            for conf_file in all_conf_files.values():
                if not conf_file['node_ids'] and not conf_file['nodegroup_ids']:
                    conf_files[conf_file['dest']] = conf_file

            # If a node belongs to multiple node
            # groups for which the same configuration file is defined,
            # it is undefined which one takes precedence.
            for nodegroup in nodegroups:
                for conf_file_id in nodegroup['conf_file_ids']:
                    if conf_file_id in all_conf_files:
                        conf_files[conf_file['dest']] = all_conf_files[conf_file_id]

            # Node configuration files always take precedence over
            # node group configuration files.
            for conf_file_id in node['conf_file_ids']:
                if conf_file_id in all_conf_files:
                    conf_files[conf_file['dest']] = all_conf_files[conf_file_id]

            slivers = []
            for slice in map(lambda id: all_slices[id], node['slice_ids']):
                keys = []
                for person in map(lambda id: all_persons[id], slice['person_ids']):
                    keys += [{'key_type': all_keys[key_id]['key_type'],
                              'key': all_keys[key_id]['key']} \
                             for key_id in person['key_ids']]

                attributes = {}
                for slice_attribute in map(lambda id: all_slice_attributes[id],
                                           slice['slice_attribute_ids']):
                    # Per-node sliver attributes (slice attributes
                    # with non-null node_id fields) take precedence
                    # over global slice attributes.
                    if not attributes.has_key(slice_attribute['name']) or \
                       slice_attribute['node_id'] is not None:
                        attributes[slice_attribute['name']] = {
                            'name': slice_attribute['name'],
                            'value': slice_attribute['value']
                            }

                slivers.append({
                    'name': slice['name'],
                    'slice_id': slice['slice_id'],
                    'instantiation': slice['instantiation'],
                    'expires': slice['expires'],
                    'keys': keys,
                    'attributes': attributes.values()
                    })

            nodes.append({
                'timestamp': timestamp,
                'node_id': node['node_id'],
                'hostname': node['hostname'],
                'networks': networks,
                'groups': groups,
                'conf_files': conf_files.values(),
                'slivers': slivers
                })

        return nodes

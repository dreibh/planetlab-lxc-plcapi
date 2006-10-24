import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Slices import Slice, Slices
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.SliceAttributes import SliceAttribute, SliceAttributes

class GetSlivers(Method):
    """
    Returns an array of structs representing slivers (slices bound to
    nodes). If node_id_or_hostname_list is specified, only slivers
    bound to the specified nodes are queried.

    All of the information returned by this call can be gathered from
    other calls, e.g. GetNodes, GetNodeNetworks, GetSlices, etc. This
    function exists primarily for the benefit of Node Manager and
    Federation Manager.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        [Mixed(Node.fields['node_id'],
               Node.fields['hostname'])]
        ]

    returns = [{
        'timestamp': Parameter(int, "Timestamp of this call, in seconds since UNIX epoch"),
        'node_id': Node.fields['node_id'],
        'hostname': Node.fields['hostname'],
        'boot_state': Node.fields['boot_state'],
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

    def call(self, auth, node_id_or_hostname_list = None):
        timestamp = int(time.time())

        all_nodes = Nodes(self.api, node_id_or_hostname_list)

        nodenetwork_ids = set()
        nodegroup_ids = set()
        conf_file_ids = set()
        slice_ids = set()
        for node_id, node in all_nodes.iteritems():
            nodenetwork_ids.update(node['nodenetwork_ids'])
            nodegroup_ids.update(node['nodegroup_ids'])
            conf_file_ids.update(node['conf_file_ids'])
            slice_ids.update(node['slice_ids'])

        # Get nodenetwork information
        if nodenetwork_ids:
            all_nodenetworks = NodeNetworks(self.api, nodenetwork_ids)
        else:
            all_nodenetworks = {}

        # Get node group information
        if nodegroup_ids:
            all_nodegroups = NodeGroups(self.api, nodegroup_ids)

            for nodegroup_id, nodegroup in all_nodegroups.iteritems():
                conf_file_ids.update(nodegroup['conf_file_ids'])
        else:
            all_nodegroups = {}

        # Get configuration files
        if conf_file_ids:
            all_conf_files = ConfFiles(self.api, conf_file_ids)
        else:
            all_conf_files = {}

        if slice_ids:
            # Get slices
            all_slices = Slices(self.api, slice_ids)

            person_ids = set()
            slice_attribute_ids = set()
            for slice_id, slice in all_slices.iteritems():
                person_ids.update(slice['person_ids'])
                slice_attribute_ids.update(slice['slice_attribute_ids'])

            # Get user accounts
            all_persons = Persons(self.api, person_ids)

            key_ids = set()
            for person_id, person in all_persons.iteritems():
                key_ids.update(person['key_ids'])

            # Get user account keys
            all_keys = Keys(self.api, key_ids)

            # Get slice attributes
            all_slice_attributes = SliceAttributes(self.api, slice_attribute_ids)

        nodes = []
        for node_id, node in all_nodes.iteritems():
            networks = [all_nodenetworks[nodenetwork_id] for nodenetwork_id in node['nodenetwork_ids']]
            nodegroups = [all_nodegroups[nodegroup_id] for nodegroup_id in node['nodegroup_ids']]
            groups = [nodegroup['name'] for nodegroup in nodegroups]

            # If a node belongs to multiple node
            # groups for which the same configuration file is defined,
            # it is undefined which one takes precedence.
            conf_files = {}
            for nodegroup in nodegroups:
                for conf_file in map(lambda id: all_conf_files[id], nodegroup['conf_file_ids']):
                    conf_files[conf_file['dest']] = conf_file

            # Node configuration files always take precedence over
            # node group configuration files.
            for conf_file in map(lambda id: all_conf_files[id], node['conf_file_ids']):
                conf_files[conf_file['dest']] = conf_file

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

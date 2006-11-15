from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Auth import Auth

class AddSliceAttribute(Method):
    """
    Sets the specified attribute of the slice (or sliver, if
    node_id_or_hostname is specified) to the specified value.

    Attributes may require the caller to have a particular role in
    order to be set or changed. Users may only set attributes of
    slices or slivers of which they are members. PIs may only set
    attributes of slices or slivers at their sites, or of which they
    are members. Admins may set attributes of any slice or sliver.

    Returns the new slice_attribute_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Mixed(SliceAttribute.fields['slice_id'],
              SliceAttribute.fields['name']),
        Mixed(SliceAttribute.fields['attribute_type_id'],
              SliceAttribute.fields['name']),
        SliceAttribute.fields['value'],
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = Parameter(int, 'New slice_attribute_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'SliceAttribute'

    def call(self, auth, slice_id_or_name, attribute_type_id_or_name, value, node_id_or_hostname = None):
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        attribute_types = SliceAttributeTypes(self.api, [attribute_type_id_or_name])
        if not attribute_types:
            raise PLCInvalidArgument, "No such slice attribute type"
        attribute_type = attribute_types[0]

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

            if attribute_type['min_role_id'] is not None and \
               min(self.caller['role_ids']) > attribute_type['min_role_id']:
                raise PLCPermissionDenied, "Not allowed to set the specified slice attribute"

        slice_attribute = SliceAttribute(self.api)
        slice_attribute['slice_id'] = slice['slice_id']
        slice_attribute['attribute_type_id'] = attribute_type['attribute_type_id']
        slice_attribute['value'] = value

        # Sliver attribute if node is specified
        if node_id_or_hostname is not None:
            nodes = Nodes(self.api, [node_id_or_hostname])
            if not nodes:
                raise PLCInvalidArgument, "No such node"
            node = nodes[0]
            
            if node['node_id'] not in slice['node_ids']:
                raise PLCInvalidArgument, "Node not in the specified slice"

            slice_attribute['node_id'] = node['node_id']

        slice_attribute.sync()
	self.object_ids = [slice_attribute['slice_attribute_id']]

        return slice_attribute['slice_attribute_id']

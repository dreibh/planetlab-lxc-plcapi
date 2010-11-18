#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row

from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.TagTypes import TagTypes
from PLC.InterfaceTags import InterfaceTags
from PLC.Methods.AddInterfaceTag import AddInterfaceTag
from PLC.Methods.UpdateInterfaceTag import UpdateInterfaceTag

cannot_update = ['interface_id', 'node_id']

class AddInterface(Method):
    """

    Adds a new network for a node. Any values specified in
    interface_fields are used, otherwise defaults are
    used.

    If type is static, then ip, gateway, network, broadcast, netmask,
    and dns1 must all be specified in interface_fields. If type is
    dhcp, these parameters, even if specified, are ignored.

    PIs and techs may only add interfaces to their own nodes. Admins may
    add interfaces to any node.

    Returns the new interface_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepted_fields = Row.accepted_fields(cannot_update, Interface.fields, exclude=True)
    accepted_fields.update(Interface.tags)

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        accepted_fields
        ]

    returns = Parameter(int, 'New interface_id (> 0) if successful')


    def call(self, auth, node_id_or_hostname, interface_fields):

        [native,tags,rejected]=Row.split_fields(interface_fields,[Interface.fields,Interface.tags])

        # type checking
        native = Row.check_fields (native, self.accepted_fields)
        if rejected:
            raise PLCInvalidArgument, "Cannot add Interface with column(s) %r"%rejected

        # Check if node exists
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id_or_hostname
        node = nodes[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site where the node exists.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to add an interface to the specified node"

        # Add interface
        interface = Interface(self.api, native)
        interface['node_id'] = node['node_id']
        # if this is the first interface, make it primary
        if not node['interface_ids']:
            interface['is_primary'] = True
        interface.sync()

        # Logging variables
        self.event_objects = { 'Node': [node['node_id']],
                               'Interface' : [interface['interface_id']] }
        self.message = "Interface %d added" % interface['interface_id']

        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            if not TagTypes(self.api,{'tagname':tagname}):
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            interface_tags=InterfaceTags(self.api,{'tagname':tagname,'interface_id':interface['interface_id']})
            if not interface_tags:
                AddInterfaceTag(self.api).__call__(auth,interface['interface_id'],tagname,value)
            else:
                UpdateInterfaceTag(self.api).__call__(auth,interface_tags[0]['interface_tag_id'],value)

        return interface['interface_id']

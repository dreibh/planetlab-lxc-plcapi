from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row
from PLC.Auth import Auth

from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagTypes
from PLC.InterfaceTags import InterfaceTags
from PLC.Interfaces import Interface, Interfaces
from PLC.Methods.AddInterfaceTag import AddInterfaceTag
from PLC.Methods.UpdateInterfaceTag import UpdateInterfaceTag

cannot_update = ['interface_id','node_id']

class UpdateInterface(Method):
    """
    Updates an existing interface network. Any values specified in
    interface_fields are used, otherwise defaults are
    used. Acceptable values for method are dhcp and static. If type is
    static, then ip, gateway, network, broadcast, netmask, and dns1
    must all be specified in interface_fields. If type is dhcp,
    these parameters, even if specified, are ignored.

    PIs and techs may only update interfaces associated with their own
    nodes. Admins may update any interface network.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepted_fields = Row.accepted_fields(cannot_update, Interface.fields,exclude=True)
    accepted_fields.update(Interface.tags)

    accepts = [
        Auth(),
        Interface.fields['interface_id'],
        accepted_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, interface_id, interface_fields):

        [native,tags,rejected] = Row.split_fields(interface_fields,[Interface.fields,Interface.tags])

        # type checking
        native= Row.check_fields (native, self.accepted_fields)
        if rejected:
            raise PLCInvalidArgument, "Cannot update Interface column(s) %r"%rejected

        # Get interface information
        interfaces = Interfaces(self.api, [interface_id])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface"

        interface = interfaces[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site where the node exists.
        if 'admin' not in self.caller['roles']:
            nodes = Nodes(self.api, [interface['node_id']])
            if not nodes:
                raise PLCPermissionDenied, "Interface is not associated with a node"
            node = nodes[0]
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to update interface"

        interface.update(native)
        interface.update_last_updated(commit=False)
        interface.sync()

        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            if not TagTypes(self.api,{'tagname':tagname}):
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            interface_tags=InterfaceTags(self.api,{'tagname':tagname,'interface_id':interface['interface_id']})
            if not interface_tags:
                AddInterfaceTag(self.api).__call__(auth,interface['interface_id'],tagname,value)
            else:
                UpdateInterfaceTag(self.api).__call__(auth,interface_tags[0]['interface_tag_id'],value)

        self.event_objects = {'Interface': [interface['interface_id']]}
        if 'ip' in interface:
            self.message = "Interface %s updated"%interface['ip']
        else:
            self.message = "Interface %d updated"%interface['interface_id']
        self.message += "[%s]." % ", ".join(interface_fields.keys())

        return 1

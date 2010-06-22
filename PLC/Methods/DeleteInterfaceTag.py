# $Id$
# $URL$
#
# Thierry Parmentelat - INRIA
#
# $Revision$
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.InterfaceTags import InterfaceTag, InterfaceTags
from PLC.Interfaces import Interface, Interfaces

from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites

class DeleteInterfaceTag(Method):
    """
    Deletes the specified interface setting

    Attributes may require the caller to have a particular role in order
    to be deleted, depending on the related tag type.
    Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        InterfaceTag.fields['interface_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Interface'


    def call(self, auth, interface_tag_id):
        interface_tags = InterfaceTags(self.api, [interface_tag_id])
        if not interface_tags:
            raise PLCInvalidArgument, "No such interface tag %r"%interface_tag_id
        interface_tag = interface_tags[0]

        ### reproducing a check from UpdateSliceTag, looks dumb though
        interfaces = Interfaces(self.api, [interface_tag['interface_id']])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface %r"%interface_tag['interface_id']
        interface = interfaces[0]

        assert interface_tag['interface_tag_id'] in interface['interface_tag_ids']

        # check permission : it not admin, is the user affiliated with the right site
        if 'admin' not in self.caller['roles']:
            # locate node
            node = Nodes (self.api,[interface['node_id']])[0]
            # locate site
            site = Sites (self.api, [node['site_id']])[0]
            # check caller is affiliated with this site
            if self.caller['person_id'] not in site['person_ids']:
                raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']

            required_min_role = tag_type ['min_role_id']
            if required_min_role is not None and \
                    min(self.caller['role_ids']) > required_min_role:
                raise PLCPermissionDenied, "Not allowed to modify the specified interface setting, requires role %d",required_min_role

        interface_tag.delete()
        self.object_ids = [interface_tag['interface_tag_id']]

        return 1

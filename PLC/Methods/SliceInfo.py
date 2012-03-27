from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Faults import *
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Nodes import Node, Nodes

class SliceInfo(Method):
    """
    Deprecated. Can be implemented with GetSlices.

    Returns an array of structs containing details about slices.
    The summary can optionally include the list of nodes in and
    users of each slice.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins may query any
    slice. If a slice that cannot be queried is specified in
    slice_filter, details about that slice will not be returned.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        [Mixed(Slice.fields['name'])],
        Parameter(bool, "Whether or not to return users for the slices", nullok = True),
        Parameter(bool, "Whether or not to return nodes for the slices", nullok = True)
        ]

    returns = [Slice.fields]


    def call(self, auth, slice_name_list=None, return_users=None, return_nodes=None):
        # If we are not admin, make sure to return only viewable
        # slices.
        slice_filter = slice_name_list
        slices = Slices(self.api, slice_filter)
        if not slices:
            raise PLCInvalidArgument, "No such slice"

        if 'admin' not in self.caller['roles']:
            # Get slices that we are able to view
            valid_slice_ids = self.caller['slice_ids']
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_slice_ids += site['slice_ids']

            if not valid_slice_ids:
                return []

            slices = filter(lambda slice: slice['slice_id'] in valid_slice_ids, slices)


        for slice in slices:
            index = slices.index(slice)
            node_ids = slices[index].pop('node_ids')
            person_ids = slices[index].pop('person_ids')
            if return_users or return_users is None:
                persons = Persons(self.api, person_ids)
                emails = [person['email'] for person in persons]
                slices[index]['users'] = emails
            if return_nodes or return_nodes is None:
                nodes = Nodes(self.api, node_ids)
                hostnames = [node['hostname'] for node in nodes]
                slices[index]['nodes'] = hostnames


        return slices

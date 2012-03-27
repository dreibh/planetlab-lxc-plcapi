# Thierry Parmentelat -- INRIA

from PLC.Faults import *
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row

from PLC.Leases import Leases, Lease
from PLC.Nodes import Nodes, Node
from PLC.Slices import Slices, Slice
from PLC.Timestamp import Timestamp

can_update = ['name', 'instantiation', 'url', 'description', 'max_nodes']

class AddLeases(Method):
    """
    Adds a new lease.
    Mandatory arguments are node(s), slice, t_from and t_until
    times can be either integers, datetime's, or human readable (see Timestamp)

    PIs may only add leases associated with their own sites (i.e.,
    to a slice that belongs to their site).
    Users may only add leases associated with their own slices.

    Returns the new lease_ids if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],[Node.fields['node_id']],
              Node.fields['hostname'],[Node.fields['hostname']],),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        Mixed(Lease.fields['t_from']),
        Mixed(Lease.fields['t_until']),
        ]

    returns = Parameter(dict, " 'new_ids' is the list of newly created ids, 'errors' is a list of error strings")

    def call(self, auth, node_id_or_hostname_s, slice_id_or_name, t_from, t_until):

        # xxx - round to plain hours somewhere

        # Get node information
        nodes = Nodes(self.api, node_id_or_hostname_s)
        if not nodes:
            raise PLCInvalidArgument, "No such node(s) %r"%node_id_or_hostname_s
        for node in nodes:
            if node['node_type'] != 'reservable':
                raise PLCInvalidArgument, "Node %s is not reservable"%node['hostname']

        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice %r"%slice_id_or_name
        slice = slices[0]

        # check access
        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

        # normalize timestamps
        t_from = Timestamp.sql_validate_utc(t_from)
        t_until = Timestamp.sql_validate_utc(t_until)

        ########## create stuff
        errors=[]
        result_ids=[]
        for node in nodes:
            if node['peer_id'] is not None:
                errors.append("Cannot set lease on remote node %r"%node['hostname'])
                continue
            # let the DB check for time consistency
            try:
                lease = Lease (self.api, {'node_id':node['node_id'], 'slice_id': slice['slice_id'],
                                          't_from':t_from, 't_until':t_until})
                lease.sync()
                result_ids.append(lease['lease_id'])
            except Exception,e:
                errors.append("Could not create lease on n=%s s=%s [%s .. %s] -- %r" % \
                                  (node['hostname'],slice['name'],t_from,t_until,e))
                nodes.remove(node)

        self.event_objects = {'Slice': [slice['slice_id']],
                              'Node': [node['node_id'] for node in nodes]}
        self.message = "New leases %r on n=%r s=%s [%s -> %s]" % \
            (result_ids,[node['hostname'] for node in nodes],slice['name'],t_from,t_until)

        return {'new_ids': result_ids,
                'errors': errors}

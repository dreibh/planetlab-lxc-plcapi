#
# Functions for interacting with the interfaces table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from types import StringTypes
import socket
import struct

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.NetworkTypes import NetworkType, NetworkTypes
from PLC.NetworkMethods import NetworkMethod, NetworkMethods
import PLC.Nodes

def valid_ipv4(ip):
    try:
        ip = socket.inet_ntoa(socket.inet_aton(ip))
        return True
    except socket.error:
        return False

def valid_ipv6(ip):
    try:
        ip = socket.inet_ntop(socket.AF_INET6, socket.inet_pton(socket.AF_INET6, ip))
        return True
    except socket.error:
        return False   

def valid_ip(ip):
    return valid_ipv4(ip) or valid_ipv6(ip)

def in_same_network_ipv4(address1, address2, netmask):
    """
    Returns True if two IPv4 addresses are in the same network. Faults
    if an address is invalid.
    """
    address1 = struct.unpack('>L', socket.inet_aton(address1))[0]
    address2 = struct.unpack('>L', socket.inet_aton(address2))[0]
    netmask = struct.unpack('>L', socket.inet_aton(netmask))[0]

    return (address1 & netmask) == (address2 & netmask)

def in_same_network_ipv6(address1, address2, netmask):
    """
    Returns True if two IPv6 addresses are in the same network. Faults
    if an address is invalid.
    """
    address1 = struct.unpack('>2Q', socket.inet_pton(socket.AF_INET6, address1))[0]
    address2 = struct.unpack('>2Q', socket.inet_pton(socket.AF_INET6, address2))[0]
    netmask = struct.unpack('>2Q', socket.inet_pton(socket.AF_INET6, netmask))[0]

    return (address1 & netmask) == (address2 & netmask)

def in_same_network(address1, address2, netmask):
    return in_same_network_ipv4(address1, address2, netmask) or \
           in_same_network_ipv6(address1, address2, netmask) 

class Interface(Row):
    """
    Representation of a row in the interfaces table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'interfaces'
    primary_key = 'interface_id'
    join_tables = ['interface_tag']
    fields = {
        'interface_id': Parameter(int, "Node interface identifier"),
        'method': Parameter(str, "Addressing method (e.g., 'static' or 'dhcp')"),
        'type': Parameter(str, "Address type (e.g., 'ipv4')"),
        'ip': Parameter(str, "IP address", nullok = True),
        'mac': Parameter(str, "MAC address", nullok = True),
        'gateway': Parameter(str, "IP address of primary gateway", nullok = True),
        'network': Parameter(str, "Subnet address", nullok = True),
        'broadcast': Parameter(str, "Network broadcast address", nullok = True),
        'netmask': Parameter(str, "Subnet mask", nullok = True),
        'dns1': Parameter(str, "IP address of primary DNS server", nullok = True),
        'dns2': Parameter(str, "IP address of secondary DNS server", nullok = True),
        'bwlimit': Parameter(int, "Bandwidth limit", min = 0, nullok = True),
        'hostname': Parameter(str, "(Optional) Hostname", nullok = True),
        'node_id': Parameter(int, "Node associated with this interface"),
        'is_primary': Parameter(bool, "Is the primary interface for this node"),
        'interface_tag_ids' : Parameter([int], "List of interface settings"),
        'last_updated': Parameter(int, "Date and time when node entry was created", ro = True),
        }

    view_tags_name = "view_interface_tags"
    tags = {}

    def validate_method(self, method):
        network_methods = [row['method'] for row in NetworkMethods(self.api)]
        if method not in network_methods:
            raise PLCInvalidArgument, "Invalid addressing method %s"%method
        return method

    def validate_type(self, type):
        network_types = [row['type'] for row in NetworkTypes(self.api)]
        if type not in network_types:
            raise PLCInvalidArgument, "Invalid address type %s"%type
        return type

    def validate_ip(self, ip):
        if ip and not valid_ip(ip):
            raise PLCInvalidArgument, "Invalid IP address %s"%ip
        return ip

    def validate_mac(self, mac):
        if not mac:
            return mac

        try:
            bytes = mac.split(":")
            if len(bytes) < 6:
                raise Exception
            for i, byte in enumerate(bytes):
                byte = int(byte, 16)
                if byte < 0 or byte > 255:
                    raise Exception
                bytes[i] = "%02x" % byte
            mac = ":".join(bytes)
        except:
            raise PLCInvalidArgument, "Invalid MAC address %s"%mac

        return mac

    validate_gateway = validate_ip
    validate_network = validate_ip
    validate_broadcast = validate_ip
    validate_netmask = validate_ip
    validate_dns1 = validate_ip
    validate_dns2 = validate_ip

    def validate_bwlimit(self, bwlimit):
        if not bwlimit:
            return bwlimit

        if bwlimit < 500000:
            raise PLCInvalidArgument, 'Minimum bw is 500 kbs'

        return bwlimit

    def validate_hostname(self, hostname):
        # Optional
        if not hostname:
            return hostname

        if not PLC.Nodes.valid_hostname(hostname):
            raise PLCInvalidArgument, "Invalid hostname %s"%hostname

        return hostname

    def validate_node_id(self, node_id):
        nodes = PLC.Nodes.Nodes(self.api, [node_id])
        if not nodes:
            raise PLCInvalidArgument, "No such node %d"%node_id

        return node_id

    def validate_is_primary(self, is_primary):
        """
        Set this interface to be the primary one.
        """

        if is_primary:
            nodes = PLC.Nodes.Nodes(self.api, [self['node_id']])
            if not nodes:
                raise PLCInvalidArgument, "No such node %d"%node_id
            node = nodes[0]

            if node['interface_ids']:
                conflicts = Interfaces(self.api, node['interface_ids'])
                for interface in conflicts:
                    if ('interface_id' not in self or \
                        self['interface_id'] != interface['interface_id']) and \
                       interface['is_primary']:
                        raise PLCInvalidArgument, "Can only set one primary interface per node"

        return is_primary

    def validate(self):
        """
        Flush changes back to the database.
        """

        # Basic validation
        Row.validate(self)

        assert 'method' in self
        method = self['method']

        if method == "proxy" or method == "tap":
            if 'mac' in self and self['mac']:
                raise PLCInvalidArgument, "For %s method, mac should not be specified" % method
            if 'ip' not in self or not self['ip']:
                raise PLCInvalidArgument, "For %s method, ip is required" % method
            if method == "tap" and ('gateway' not in self or not self['gateway']):
                raise PLCInvalidArgument, "For tap method, gateway is required and should be " \
                      "the IP address of the node that proxies for this address"
            # Should check that the proxy address is reachable, but
            # there's no way to tell if the only primary interface is
            # DHCP!

        elif method == "static":
            if self['type'] == 'ipv4':
                for key in ['gateway', 'dns1']:
                    if key not in self or not self[key]:
                        if 'is_primary' in self and self['is_primary'] is True:
                            raise PLCInvalidArgument, "For static method primary network, %s is required" % key
                    else:
                        globals()[key] = self[key]
                for key in ['ip', 'network', 'broadcast', 'netmask']:
                    if key not in self or not self[key]:
                        raise PLCInvalidArgument, "For static method, %s is required" % key
                    globals()[key] = self[key]
                if not in_same_network(ip, network, netmask):
                    raise PLCInvalidArgument, "IP address %s is inconsistent with network %s/%s" % \
                          (ip, network, netmask)
                if not in_same_network(broadcast, network, netmask):
                    raise PLCInvalidArgument, "Broadcast address %s is inconsistent with network %s/%s" % \
                          (broadcast, network, netmask)
                if 'gateway' in globals() and not in_same_network(ip, gateway, netmask):
                    raise PLCInvalidArgument, "Gateway %s is not reachable from %s/%s" % \
                          (gateway, ip, netmask)
            elif self['type'] == 'ipv6':
                for key in ['ip', 'gateway']:
                    if key not in self or not self[key]:
                        raise PLCInvalidArgument, "For static ipv6 method, %s is required" % key
                    globals()[key] = self[key]
        elif method == "ipmi":
            if 'ip' not in self or not self['ip']:
                raise PLCInvalidArgument, "For ipmi method, ip is required"

    validate_last_updated = Row.validate_timestamp

    def update_timestamp(self, col_name, commit = True):
        """
        Update col_name field with current time
        """

        assert 'interface_id' in self
        assert self.table_name

        self.api.db.do("UPDATE %s SET %s = CURRENT_TIMESTAMP " % (self.table_name, col_name) + \
                       " where interface_id = %d" % (self['interface_id']) )
        self.sync(commit)

    def update_last_updated(self, commit = True):
        self.update_timestamp('last_updated', commit)

    def delete(self,commit=True):
        ### need to cleanup ilinks
        self.api.db.do("DELETE FROM ilink WHERE src_interface_id=%d OR dst_interface_id=%d" % \
                           (self['interface_id'],self['interface_id']))
        
        Row.delete(self)

class Interfaces(Table):
    """
    Representation of row(s) from the interfaces table in the
    database.
    """

    def __init__(self, api, interface_filter = None, columns = None):
        Table.__init__(self, api, Interface, columns)

        # the view that we're selecting upon: start with view_nodes
        view = "view_interfaces"
        # as many left joins as requested tags
        for tagname in self.tag_columns:
            view= "%s left join %s using (%s)"%(view,Interface.tagvalue_view_name(tagname),
                                                Interface.primary_key)

        sql = "SELECT %s FROM %s WHERE True" % \
            (", ".join(self.columns.keys()+self.tag_columns.keys()),view)

        if interface_filter is not None:
            if isinstance(interface_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), interface_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), interface_filter)
                interface_filter = Filter(Interface.fields, {'interface_id': ints, 'ip': strs})
                sql += " AND (%s) %s" % interface_filter.sql(api, "OR")
            elif isinstance(interface_filter, dict):
                allowed_fields=dict(Interface.fields.items()+Interface.tags.items())
                interface_filter = Filter(allowed_fields, interface_filter)
                sql += " AND (%s) %s" % interface_filter.sql(api)
            elif isinstance(interface_filter, int):
                interface_filter = Filter(Interface.fields, {'interface_id': [interface_filter]})
                sql += " AND (%s) %s" % interface_filter.sql(api)
            elif isinstance (interface_filter, StringTypes):
                interface_filter = Filter(Interface.fields, {'ip':[interface_filter]})
                sql += " AND (%s) %s" % interface_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong interface filter %r"%interface_filter

        self.selectall(sql)

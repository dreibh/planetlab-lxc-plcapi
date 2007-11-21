#
# Functions for interacting with the nodenetworks table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
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

def valid_ip(ip):
    try:
        ip = socket.inet_ntoa(socket.inet_aton(ip))
        return True
    except socket.error:
        return False

def in_same_network(address1, address2, netmask):
    """
    Returns True if two IPv4 addresses are in the same network. Faults
    if an address is invalid.
    """

    address1 = struct.unpack('>L', socket.inet_aton(address1))[0]
    address2 = struct.unpack('>L', socket.inet_aton(address2))[0]
    netmask = struct.unpack('>L', socket.inet_aton(netmask))[0]

    return (address1 & netmask) == (address2 & netmask)

class NodeNetwork(Row):
    """
    Representation of a row in the nodenetworks table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'nodenetworks'
    primary_key = 'nodenetwork_id'
    join_tables = ['nodenetwork_setting']
    fields = {
        'nodenetwork_id': Parameter(int, "Node interface identifier"),
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
        'nodenetwork_setting_ids' : Parameter([int], "List of nodenetwork settings"),
        }

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

            if node['nodenetwork_ids']:
                conflicts = NodeNetworks(self.api, node['nodenetwork_ids'])
                for nodenetwork in conflicts:
                    if ('nodenetwork_id' not in self or \
                        self['nodenetwork_id'] != nodenetwork['nodenetwork_id']) and \
                       nodenetwork['is_primary']:
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
  	    if 'gateway' not in self or self['gateway'] is None:
		if 'is_primary' in self and self['is_primary'] is True:
		    raise PLCInvalidArgument, "For static method primary network, gateway is required"
            for key in ['ip', 'network', 'broadcast', 'netmask', 'dns1']:
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

        elif method == "ipmi":
            if 'ip' not in self or not self['ip']:
                raise PLCInvalidArgument, "For ipmi method, ip is required"

class NodeNetworks(Table):
    """
    Representation of row(s) from the nodenetworks table in the
    database.
    """

    def __init__(self, api, nodenetwork_filter = None, columns = None):
        Table.__init__(self, api, NodeNetwork, columns)

        sql = "SELECT %s FROM view_nodenetworks WHERE True" % \
              ", ".join(self.columns)

        if nodenetwork_filter is not None:
            if isinstance(nodenetwork_filter, (list, tuple, set)):
                nodenetwork_filter = Filter(NodeNetwork.fields, {'nodenetwork_id': nodenetwork_filter})
            elif isinstance(nodenetwork_filter, dict):
                nodenetwork_filter = Filter(NodeNetwork.fields, nodenetwork_filter)
            elif isinstance(nodenetwork_filter, int):
                nodenetwork_filter = Filter(NodeNetwork.fields, {'nodenetwork_id': [nodenetwork_filter]})
            else:
                raise PLCInvalidArgument, "Wrong node network filter %r"%nodenetwork_filter
            sql += " AND (%s) %s" % nodenetwork_filter.sql(api)

        self.selectall(sql)

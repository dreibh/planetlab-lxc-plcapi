#
# Functions for interacting with the nodenetworks table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: NodeNetworks.py,v 1.10 2006/10/24 20:02:22 mlhuang Exp $
#

from types import StringTypes
import socket
import struct

from PLC.Faults import *
from PLC.Parameter import Parameter
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
    fields = {
        'nodenetwork_id': Parameter(int, "Node interface identifier"),
        'method': Parameter(str, "Addressing method (e.g., 'static' or 'dhcp')"),
        'type': Parameter(str, "Address type (e.g., 'ipv4')"),
        'ip': Parameter(str, "IP address"),
        'mac': Parameter(str, "MAC address"),
        'gateway': Parameter(str, "IP address of primary gateway"),
        'network': Parameter(str, "Subnet address"),
        'broadcast': Parameter(str, "Network broadcast address"),
        'netmask': Parameter(str, "Subnet mask"),
        'dns1': Parameter(str, "IP address of primary DNS server"),
        'dns2': Parameter(str, "IP address of secondary DNS server"),
        'bwlimit': Parameter(int, "Bandwidth limit", min = 0),
        'hostname': Parameter(str, "(Optional) Hostname"),
        'node_id': Parameter(int, "Node associated with this interface"),
        'is_primary': Parameter(bool, "Is the primary interface for this node"),
        }

    def validate_method(self, method):
        if method not in NetworkMethods(self.api):
            raise PLCInvalidArgument, "Invalid addressing method"
	return method

    def validate_type(self, type):
        if type not in NetworkTypes(self.api):
            raise PLCInvalidArgument, "Invalid address type"
	return type

    def validate_ip(self, ip):
        if ip and not valid_ip(ip):
            raise PLCInvalidArgument, "Invalid IP address " + ip
        return ip

    def validate_mac(self, mac):
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
            raise PLCInvalidArgument, "Invalid MAC address"

        return mac

    validate_gateway = validate_ip
    validate_network = validate_ip
    validate_broadcast = validate_ip
    validate_netmask = validate_ip
    validate_dns1 = validate_ip
    validate_dns2 = validate_ip

    def validate_hostname(self, hostname):
        # Optional
        if not hostname:
            return hostname

        if not PLC.Nodes.valid_hostname(hostname):
            raise PLCInvalidArgument, "Invalid hostname"

        return hostname

    def validate_node_id(self, node_id):
        nodes = PLC.Nodes.Nodes(self.api, [node_id])
        if not nodes:
            raise PLCInvalidArgument, "No such node"

        return node_id

    def validate_is_primary(self, is_primary):
        """
        Set this interface to be the primary one.
        """

        if is_primary:
            nodes = PLC.Nodes.Nodes(self.api, [self['node_id']]).values()
            if not nodes:
                raise PLCInvalidArgument, "No such node"
            node = nodes[0]

            if node['nodenetwork_ids']:
                conflicts = NodeNetworks(self.api, node['nodenetwork_ids'])
                for nodenetwork_id, nodenetwork in conflicts.iteritems():
                    if ('nodenetwork_id' not in self or self['nodenetwork_id'] != nodenetwork_id) and \
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
            for key in ['ip', 'gateway', 'network', 'broadcast', 'netmask', 'dns1']:
                if key not in self or not self[key]:
                    raise PLCInvalidArgument, "For static method, %s is required" % key
                globals()[key] = self[key]
            if not in_same_network(ip, network, netmask):
                raise PLCInvalidArgument, "IP address %s is inconsistent with network %s/%s" % \
                      (ip, network, netmask)
            if not in_same_network(broadcast, network, netmask):
                raise PLCInvalidArgument, "Broadcast address %s is inconsistent with network %s/%s" % \
                      (broadcast, network, netmask)
            if not in_same_network(ip, gateway, netmask):
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

    def __init__(self, api, nodenetwork_id_or_ip_list = None):
        self.api = api

        sql = "SELECT %s FROM nodenetworks" % \
              ", ".join(NodeNetwork.fields)

        if nodenetwork_id_or_ip_list:
            # Separate the list into integers and strings
            nodenetwork_ids = filter(lambda nodenetwork_id: isinstance(nodenetwork_id, (int, long)),
                                     nodenetwork_id_or_ip_list)
            ips = filter(lambda ip: isinstance(ip, StringTypes),
                               nodenetwork_id_or_ip_list)
            sql += " WHERE (False"
            if nodenetwork_ids:
                sql += " OR nodenetwork_id IN (%s)" % ", ".join(map(str, nodenetwork_ids))
            if ips:
                sql += " OR ip IN (%s)" % ", ".join(api.db.quote(ips)).lower()
            sql += ")"

        rows = self.api.db.selectall(sql)

        for row in rows:
            self[row['nodenetwork_id']] = NodeNetwork(api, row)

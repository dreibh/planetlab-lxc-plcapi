#
# Functions for interacting with the nodenetworks table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: NodeNetworks.py,v 1.3 2006/09/19 19:35:05 mlhuang Exp $
#

from types import StringTypes
import socket
import struct

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table
import PLC.Nodes

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
        # XXX Should be an int (bps)
        'bwlimit': Parameter(str, "Bandwidth limit"),
        'hostname': Parameter(str, "(Optional) Hostname"),
        'node_id': Parameter(int, "Node associated with this interface (if any)"),
        'is_primary': Parameter(bool, "Is the primary interface for this node"),
        }

    methods = ['static', 'dhcp', 'proxy', 'tap', 'ipmi', 'unknown']

    types = ['ipv4']

    bwlimits = ['-1',
                '100kbit', '250kbit', '500kbit',
                '1mbit', '2mbit', '5mbit',
                '10mbit', '20mbit', '50mbit',
                '100mbit']

    def __init__(self, api, fields):
        Row.__init__(self, fields)
        self.api = api

    def validate_method(self, method):
        if method not in self.methods:
            raise PLCInvalidArgument, "Invalid addressing method"
	return method

    def validate_type(self, type):
        if type not in self.types:
            raise PLCInvalidArgument, "Invalid address type"
	return type

    def validate_ip(self, ip):
        if ip:
            try:
                ip = socket.inet_ntoa(socket.inet_aton(ip))
            except socket.error:
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

    def validate_bwlimit(self, bwlimit):
        if bwlimit not in self.bwlimits:
            raise PLCInvalidArgument, "Invalid bandwidth limit"
	return bwlimit

    def validate_hostname(self, hostname):
        # Optional
        if not hostname:
            return hostname

        # Validate hostname, and check for conflicts with a node hostname
        return PLC.Nodes.Node.validate_hostname(self, hostname)

    def sync(self, commit = True):
        """
        Flush changes back to the database.
        """

        # Validate all specified fields
        self.validate()

        try:
            method = self['method']
            self['type']
        except KeyError:
            raise PLCInvalidArgument, "method and type must both be specified"

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

        # Fetch a new nodenetwork_id if necessary
        if 'nodenetwork_id' not in self:
            rows = self.api.db.selectall("SELECT NEXTVAL('nodenetworks_nodenetwork_id_seq') AS nodenetwork_id")
            if not rows:
                raise PLCDBError("Unable to fetch new nodenetwork_id")
            self['nodenetwork_id'] = rows[0]['nodenetwork_id']
            insert = True
        else:
            insert = False

        # Filter out fields that cannot be set or updated directly
        nodenetworks_fields = self.api.db.fields('nodenetworks')
        fields = dict(filter(lambda (key, value): key in nodenetworks_fields,
                             self.items()))

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        if insert:
            # Insert new row in nodenetworks table
            sql = "INSERT INTO nodenetworks (%s) VALUES (%s)" % \
                  (", ".join(keys), ", ".join(values))
        else:
            # Update existing row in sites table
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            sql = "UPDATE nodenetworks SET " + \
                  ", ".join(columns) + \
                  " WHERE nodenetwork_id = %(nodenetwork_id)d"

        self.api.db.do(sql, fields)

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete existing nodenetwork.
        """

        assert 'nodenetwork_id' in self

        # Delete ourself
        self.api.db.do("DELETE FROM nodenetworks" \
                       " WHERE nodenetwork_id = %d" % \
                       self['nodenetwork_id'])
        
        if commit:
            self.api.db.commit()

class NodeNetworks(Table):
    """
    Representation of row(s) from the nodenetworks table in the
    database.
    """

    def __init__(self, api, nodenetwork_id_or_hostname_list = None):
        self.api = api

        # N.B.: Node IDs returned may be deleted.
        sql = "SELECT * FROM nodenetworks"

        if nodenetwork_id_or_hostname_list:
            # Separate the list into integers and strings
            nodenetwork_ids = filter(lambda nodenetwork_id: isinstance(nodenetwork_id, (int, long)),
                                     nodenetwork_id_or_hostname_list)
            hostnames = filter(lambda hostname: isinstance(hostname, StringTypes),
                               nodenetwork_id_or_hostname_list)
            sql += " WHERE (False"
            if nodenetwork_ids:
                sql += " OR nodenetwork_id IN (%s)" % ", ".join(map(str, nodenetwork_ids))
            if hostnames:
                sql += " OR hostname IN (%s)" % ", ".join(api.db.quote(hostnames)).lower()
            sql += ")"

        rows = self.api.db.selectall(sql)

        for row in rows:
            self[row['nodenetwork_id']] = NodeNetwork(api, row)

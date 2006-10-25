#!/usr/bin/env ./Shell.py
#
# Test script example
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Test.py,v 1.12 2006/10/25 14:32:31 mlhuang Exp $
#

from pprint import pprint
from string import letters, digits, punctuation
import re
import socket
import struct
import base64
import os

from random import Random
random = Random()

def randfloat(min = 0.0, max = 1.0):
    return float(min) + (random.random() * (float(max) - float(min)))

def randint(min = 0, max = 1):
    return int(randfloat(min, max + 1))

# See "2.2 Characters" in the XML specification:
#
# #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
# avoiding
# [#x7F-#x84], [#x86-#x9F], [#xFDD0-#xFDDF]

ascii_xml_chars = map(unichr, [0x9, 0xA, 0xD])
ascii_xml_chars += map(unichr, xrange(0x20, 0x7F - 1))
low_xml_chars = list(ascii_xml_chars)
low_xml_chars += map(unichr, xrange(0x84 + 1, 0x86 - 1))
low_xml_chars += map(unichr, xrange(0x9F + 1, 0xFF))
valid_xml_chars = list(low_xml_chars)
valid_xml_chars += map(unichr, xrange(0xFF + 1, 0xD7FF))
valid_xml_chars += map(unichr, xrange(0xE000, 0xFDD0 - 1))
valid_xml_chars += map(unichr, xrange(0xFDDF + 1, 0xFFFD))

def randstr(length, pool = valid_xml_chars, encoding = "utf-8"):
    sample = random.sample(pool, min(length, len(pool)))
    while True:
        s = u''.join(sample)
        bytes = len(s.encode(encoding))
        if bytes > length:
            sample.pop()
        elif bytes < length:
            sample += random.sample(pool, min(length - bytes, len(pool)))
            random.shuffle(sample)
        else:
            break
    return s

def randhostname():
    # 1. Each part begins and ends with a letter or number.
    # 2. Each part except the last can contain letters, numbers, or hyphens.
    # 3. Each part is between 1 and 64 characters, including the trailing dot.
    # 4. At least two parts.
    # 5. Last part can only contain between 2 and 6 letters.
    hostname = 'a' + randstr(61, letters + digits + '-') + '1.' + \
               'b' + randstr(61, letters + digits + '-') + '2.' + \
               'c' + randstr(5, letters)
    return hostname

def randpath(length):
    parts = []
    for i in range(randint(1, 10)):
        parts.append(randstr(randint(1, 30), ascii_xml_chars))
    return os.sep.join(parts)[0:length]

def randemail():
    return (randstr(100, letters + digits) + "@" + randhostname()).lower()

def randkey(bits = 2048):
    key_types = ["ssh-dss", "ssh-rsa"]
    key_type = random.sample(key_types, 1)[0]
    return ' '.join([key_type,
                     base64.b64encode(''.join(randstr(bits / 8).encode("utf-8"))),
                     randemail()])

def unicmp(a, b, encoding = "utf-8"):
    """
    When connected directly to the DB, values are returned as raw
    8-bit strings that may need to be decoded (as UTF-8 by default) in
    order to compare them against expected Python Unicode strings.
    """
    
    is8bit = re.compile("[\x80-\xff]").search
    if isinstance(a, str) and is8bit(a):
        a = unicode(a, encoding)
    if isinstance(b, str) and is8bit(b):
        b = unicode(b, encoding)
    return a == b

admin = {'AuthMethod': "capability",
         'Username': config.PLC_API_MAINTENANCE_USER,
         'AuthString': config.PLC_API_MAINTENANCE_PASSWORD,
         'Role': "admin"}

user = {'AuthMethod': "password",
        'Role': "user"}

pi = {'AuthMethod': "password",
      'Role': "pi"}

tech = {'AuthMethod': "password",
        'Role': "tech"}

# Add sites
site_ids = []
for i in range(3):
    def random_site():
        return {
            'name': randstr(254),
            'abbreviated_name': randstr(50),
            'login_base': randstr(20, letters).lower(),
            'latitude': int(randfloat(-90.0, 90.0) * 1000) / 1000.0,
            'longitude': int(randfloat(-180.0, 180.0) * 1000) / 1000.0,
            }
            
    # Add site
    site_fields = random_site()
    print "AddSite",
    site_id = AddSite(admin, site_fields)

    # Should return a unique site_id
    assert site_id not in site_ids
    site_ids.append(site_id)
    print "=>", site_id

    # Check site
    print "GetSites(%d)" % site_id,
    site = GetSites(admin, [site_id])[0]
    for field in site_fields:
        assert unicmp(site[field], site_fields[field])
    print "=> OK"

    # Update site
    site_fields = random_site()
    # Currently cannot change login_base
    del site_fields['login_base']
    site_fields['max_slices'] = randint(1, 10)
    print "UpdateSite(%d)" % site_id,
    UpdateSite(admin, site_id, site_fields)
    print "=> OK"

    # Check site again
    site = GetSites(admin, [site_id])[0]
    for field in site_fields:
        if field != 'login_base':
            assert unicmp(site[field], site_fields[field])

print "GetSites",
sites = GetSites(admin, site_ids)
assert set(site_ids) == set([site['site_id'] for site in sites])
print "=>", site_ids

# Add address types
address_type_ids = []
for i in range(3):
    def random_address_type():
        return {
            'name': randstr(20),
            'description': randstr(254),
            }

    print "AddAddressType",
    address_type_fields = random_address_type()
    address_type_id = AddAddressType(admin, address_type_fields)

    # Should return a unique address_type_id
    assert address_type_id not in address_type_ids
    address_type_ids.append(address_type_id)
    print "=>", address_type_id

    # Check address type
    print "GetAddressTypes(%d)" % address_type_id,
    address_type = GetAddressTypes(admin, [address_type_id])[0]
    for field in 'name', 'description':
        assert unicmp(address_type[field], address_type_fields[field])
    print "=> OK"

    # Update address type
    address_type_fields = random_address_type()
    print "UpdateAddressType(%d)" % address_type_id,
    UpdateAddressType(admin, address_type_id, address_type_fields)
    print "=> OK"

    # Check address type again
    address_type = GetAddressTypes(admin, [address_type_id])[0]
    for field in 'name', 'description':
        assert unicmp(address_type[field], address_type_fields[field])

print "GetAddressTypes",
address_types = GetAddressTypes(admin, address_type_ids)
assert set(address_type_ids) == set([address_type['address_type_id'] for address_type in address_types])
print "=>", address_type_ids

# Add site addresses
address_ids = []
for site_id in site_ids:
    for i in range(3):
        def random_address():
            return {
                'line1': randstr(254),
                'line2': randstr(254),
                'line3': randstr(254),
                'city': randstr(254),
                'state': randstr(254),
                'postalcode': randstr(64),
                'country': randstr(128),
                }

        print "AddSiteAddress",
        address_fields = random_address()
        address_id = AddSiteAddress(admin, site_id, address_fields)

        # Should return a unique address_id
        assert address_id not in address_ids
        address_ids.append(address_id)
        print "=>", address_id

        # Check address
        print "GetAddresses(%d)" % address_id,
        address = GetAddresses(admin, [address_id])[0]
        for field in address_fields:
            assert unicmp(address[field], address_fields[field])
        print "=> OK"

        # Update address
        address_fields = random_address()
        print "UpdateAddress(%d)" % address_id,
        UpdateAddress(admin, address_id, address_fields)
        print "=> OK"

        # Check address again
        address = GetAddresses(admin, [address_id])[0]
        for field in address_fields:
            assert unicmp(address[field], address_fields[field])

        # Add address types
        for address_type_id in address_type_ids:
            print "AddAddressTypeToAddress(%d, %d)" % (address_type_id, address_id),
            AddAddressTypeToAddress(admin, address_type_id, address_id)
            print "=> OK"
        
print "GetAddresses",
addresses = GetAddresses(admin, address_ids)
assert set(address_ids) == set([address['address_id'] for address in addresses])
for address in addresses:
    assert set(address_type_ids) == set(address['address_type_ids'])
print "=>", address_ids

print "GetRoles",
roles = GetRoles(admin)
role_ids = [role['role_id'] for role in roles]
roles = [role['name'] for role in roles]
roles = dict(zip(roles, role_ids))
print "=>", role_ids

print "GetKeyTypes",
key_types = GetKeyTypes(admin)
print "=>", key_types

# Add users
person_ids = []
key_ids = []
for auth in user, pi, tech:
    def random_person():
        global auth

        person_fields = {
            'first_name': randstr(128),
            'last_name': randstr(128),
            'email': randemail(),
            'bio': randstr(254),
            # Accounts are disabled by default
            'enabled': False,
            'password': randstr(254),
            }

        auth['Username'] = person_fields['email']
        auth['AuthString'] = person_fields['password']

        return person_fields

    # Add account
    person_fields = random_person()
    print "AddPerson",
    person_id = AddPerson(admin, person_fields)

    # Should return a unique person_id
    assert person_id not in person_ids
    person_ids.append(person_id)
    print "=>", person_id

    # Check account
    print "GetPersons(%d)" % person_id,
    person = GetPersons(admin, [person_id])[0]
    for field in person_fields:
        if field != 'password':
            assert unicmp(person[field], person_fields[field])
    print "=> OK"

    # Update account
    person_fields = random_person()
    print "UpdatePerson(%d)" % person_id,
    UpdatePerson(admin, person_id, person_fields)
    print "=> OK"

    # Check account again
    person = GetPersons(admin, [person_id])[0]
    for field in person_fields:
        if field != 'password':
            assert unicmp(person[field], person_fields[field])

    # Check that account is really disabled
    try:
        assert not AuthCheck(auth)
    except:
        pass

    # Add role
    role_id = roles[auth['Role']]
    print "AddRoleToPerson(%d, %d)" % (role_id, person_id),
    AddRoleToPerson(admin, role_id, person_id)
    person = GetPersons(admin, [person_id])[0]
    assert [role_id] == person['role_ids']
    print "=> OK"

    # Enable account
    UpdatePerson(admin, person_id, {'enabled': True})

    # Check authentication
    print "AuthCheck(%s)" % auth['Username'],
    assert AuthCheck(auth)
    print "=> OK"

    # Associate account with each site
    for site_id in site_ids:
        print "AddPersonToSite(%d, %d)" % (person_id, site_id),
        AddPersonToSite(admin, person_id, site_id)
        print "=> OK"

    # Make sure it really did it
    person = GetPersons(admin, [person_id])[0]
    person_site_ids = person['site_ids']
    assert set(site_ids) == set(person['site_ids'])

    # First site should be the primary site
    print "SetPersonPrimarySite(%d, %d)" % (person_id, person_site_ids[1]),
    SetPersonPrimarySite(auth, person_id, person_site_ids[1])
    person = GetPersons(admin, [person_id])[0]
    assert person['site_ids'][0] == person_site_ids[1]
    print "=> OK"

    def random_key():
        return {
            'key_type': random.sample(key_types, 1)[0],
            'key': randkey()
            }

    # Add keys
    for i in range(3):
        # Add slice attribute
        key_fields = random_key()
        print "AddPersonKey",
        key_id = AddPersonKey(admin, person_id, key_fields)

        # Should return a unique key_id
        assert key_id not in key_ids
        key_ids.append(key_id)
        print "=>", key_id

        # Check key
        print "GetKeys(%d)" % key_id,
        key = GetKeys(admin, [key_id])[0]
        for field in key_fields:
            assert unicmp(key[field], key_fields[field])
        print "=> OK"

        # Update key
        key_fields = random_key()
        print "UpdateKey(%d)" % key_id,
        UpdateKey(admin, key_id, key_fields)
        key = GetKeys(admin, [key_id])[0]
        for field in key_fields:
            assert unicmp(key[field], key_fields[field])
        print "=> OK"

    # Add and immediately blacklist a key
    key_fields = random_key()
    print "AddPersonKey",
    key_id = AddPersonKey(admin, person_id, key_fields)
    print "=>", key_id

    print "BlacklistKey(%d)" % key_id,
    BlacklistKey(admin, key_id)

    # Is effectively deleted
    assert not GetKeys(admin, [key_id])
    person = GetPersons(admin, [person_id])[0]
    assert key_id not in person['key_ids']

    # Cannot be added again
    try:
        key_id = AddPersonKey(admin, person_id, key_fields)
        assert False
    except Exception, e:
        pass

    print "=> OK"

print "GetPersons",
persons = GetPersons(admin, person_ids)
assert set(person_ids) == set([person['person_id'] for person in persons])
print "=>", person_ids

# Add node groups
nodegroup_ids = []
for i in range(3):
    def random_nodegroup():
        return {
            'name': randstr(50),
            'description': randstr(200),
            }

    # Add node group
    print "AddNodeGroup",
    nodegroup_fields = random_nodegroup()
    nodegroup_id = AddNodeGroup(admin, nodegroup_fields)

    # Should return a unique nodegroup_id
    assert nodegroup_id not in nodegroup_ids
    nodegroup_ids.append(nodegroup_id)
    print "=>", nodegroup_id

    # Check node group
    print "GetNodeGroups(%d)" % nodegroup_id,
    nodegroup = GetNodeGroups(admin, [nodegroup_id])[0]
    for field in nodegroup_fields:
        assert unicmp(nodegroup[field], nodegroup_fields[field])
    print "=> OK"

    # Update node group, with a readable name
    nodegroup_fields = random_nodegroup()
    nodegroup_fields['name'] = randstr(16, letters + ' ' + digits)
    print "UpdateNodeGroup",
    UpdateNodeGroup(admin, nodegroup_id, nodegroup_fields)
    print "=> OK"

    # Check node group again
    nodegroup = GetNodeGroups(admin, [nodegroup_id])[0]
    for field in nodegroup_fields:
        assert unicmp(nodegroup[field], nodegroup_fields[field])

print "GetNodeGroups",
nodegroups = GetNodeGroups(admin, nodegroup_ids)
assert set(nodegroup_ids) == set([nodegroup['nodegroup_id'] for nodegroup in nodegroups])
print "=>", nodegroup_ids

print "GetBootStates",
boot_states = GetBootStates(admin)
print "=>", boot_states

# Add nodes
node_ids = []
for site_id in site_ids:
    for i in range(3):
        def random_node():
            return {
                'hostname': randhostname(),
                'boot_state': random.sample(boot_states, 1)[0],
                'model': randstr(255),
                'version': randstr(64),
                }

        # Add node
        node_fields = random_node()
        print "AddNode",
        node_id = AddNode(admin, site_id, node_fields)

        # Should return a unique node_id
        assert node_id not in node_ids
        node_ids.append(node_id)
        print "=>", node_id

        # Check node
        print "GetNodes(%d)" % node_id,
        node = GetNodes(admin, [node_id])[0]
        for field in node_fields:
            assert unicmp(node[field], node_fields[field])
        print "=> OK"

        # Update node
        node_fields = random_node()
        print "UpdateNode(%d)" % node_id,
        UpdateNode(admin, node_id, node_fields)
        print "=> OK"

        # Check node again
        node = GetNodes(admin, [node_id])[0]
        for field in node_fields:
            assert unicmp(node[field], node_fields[field])

        # Add to node groups
        for nodegroup_id in nodegroup_ids:
            print "AddNodeToNodeGroup(%d, %d)" % (nodegroup_id, node_id),
            AddNodeToNodeGroup(admin, nodegroup_id, node_id)
            print "=> OK"
        
print "GetNodes",
nodes = GetNodes(admin, node_ids)
assert set(node_ids) == set([node['node_id'] for node in nodes])
print "=>", node_ids

print "GetNodeGroups",
nodegroups = GetNodeGroups(admin, nodegroup_ids)
for nodegroup in nodegroups:
    assert set(nodegroup['node_ids']) == set(node_ids)
print "=> OK"

print "GetNetworkMethods",
network_methods = GetNetworkMethods(admin)
print "=>", network_methods

print "GetNetworkTypes",
network_types = GetNetworkTypes(admin)
print "=>", network_types

# Add node networks
nodenetwork_ids = []
for node_id in node_ids:
    def random_nodenetwork(method, type):
        nodenetwork_fields = {
            'method': method,
            'type': type,
            'bwlimit': randint(500000, 10000000),
            }

        if method != 'dhcp':
            ip = randint(0, 0xffffffff)
            netmask = (0xffffffff << randint(2, 31)) & 0xffffffff
            network = ip & netmask
            broadcast = ((ip & netmask) | ~netmask) & 0xffffffff
            gateway = randint(network + 1, broadcast - 1)
            dns1 = randint(0, 0xffffffff)

            for field in 'ip', 'netmask', 'network', 'broadcast', 'gateway', 'dns1':
                nodenetwork_fields[field] = socket.inet_ntoa(struct.pack('>L', locals()[field]))

        return nodenetwork_fields

    for method in network_methods:
        for type in network_types:
            # Add node network
            print "AddNodeNetwork",
            nodenetwork_fields = random_nodenetwork(method, type)
            nodenetwork_id = AddNodeNetwork(admin, node_id, nodenetwork_fields)

            # Should return a unique nodenetwork_id
            assert nodenetwork_id not in nodenetwork_ids
            nodenetwork_ids.append(nodenetwork_id)
            print "=>", nodenetwork_id

            # Check node network
            print "GetNodeNetworks(%d)" % nodenetwork_id,
            nodenetwork = GetNodeNetworks(admin, [nodenetwork_id])[0]
            for field in nodenetwork_fields:
                assert unicmp(nodenetwork[field], nodenetwork_fields[field])
            print "=> OK"

            # Update node network
            nodenetwork_fields = random_nodenetwork(method, type)
            print "UpdateNodeNetwork(%d)" % nodenetwork_id,
            UpdateNodeNetwork(admin, nodenetwork_id, nodenetwork_fields)
            print "=> OK"

            # Check node network again
            nodenetwork = GetNodeNetworks(admin, [nodenetwork_id])[0]
            for field in nodenetwork_fields:
                assert unicmp(nodenetwork[field], nodenetwork_fields[field])

print "GetNodeNetworks",
nodenetworks = GetNodeNetworks(admin, nodenetwork_ids)
assert set(nodenetwork_ids) == set([nodenetwork['nodenetwork_id'] for nodenetwork in nodenetworks])
print "=>", nodenetwork_ids

# Add PCUs
pcu_ids = []
for site_id in site_ids:
    def random_pcu():
        return {
            'hostname': randhostname(),
            'ip': socket.inet_ntoa(struct.pack('>L', randint(0, 0xffffffff))),
            'protocol': randstr(16),
            'username': randstr(254),
            'password': randstr(254),
            'notes': randstr(254),
            'model': randstr(32),
            }

    # Add PCU
    pcu_fields = random_pcu()
    print "AddPCU",
    pcu_id = AddPCU(admin, site_id, pcu_fields)

    # Should return a unique pcu_id
    assert pcu_id not in pcu_ids
    pcu_ids.append(pcu_id)
    print "=>", pcu_id

    # Check PCU
    print "GetPCUs(%d)" % pcu_id,
    pcu = GetPCUs(admin, [pcu_id])[0]
    for field in pcu_fields:
        assert unicmp(pcu[field], pcu_fields[field])
    print "=> OK"

    # Update PCU
    pcu_fields = random_pcu()
    print "UpdatePCU(%d)" % pcu_id,
    UpdatePCU(admin, pcu_id, pcu_fields)
    print "=> OK"

    # Check PCU again
    pcu = GetPCUs(admin, [pcu_id])[0]
    for field in pcu_fields:
        assert unicmp(pcu[field], pcu_fields[field])

    # Add each node at this site to a different port on this PCU
    site = GetSites(admin, [site_id])[0]
    port = randint(1, 10)
    for node_id in site['node_ids']:
        print "AddNodeToPCU(%d, %d, %d)" % (node_id, pcu_id, port),
        AddNodeToPCU(admin, node_id, pcu_id, port)
        print "=> OK"
        port += 1

print "GetPCUs",
pcus = GetPCUs(admin, pcu_ids)
assert set(pcu_ids) == set([pcu['pcu_id'] for pcu in pcus])
print "=>", pcu_ids

# Add configuration files
conf_file_ids = []
for nodegroup_id in nodegroup_ids:
    def random_conf_file():
        return {
            'enabled': bool(randint()),
            'source': randpath(255),
            'dest': randpath(255),
            'file_permissions': "%#o" % randint(0, 512),
            'file_owner': randstr(32, letters + '_' + digits),
            'file_group': randstr(32, letters + '_' + digits),
            'preinstall_cmd': randpath(100),
            'postinstall_cmd': randpath(100),
            'error_cmd': randpath(100),
            'ignore_cmd_errors': bool(randint()),
            'always_update': bool(randint()),
            }

    # Add configuration file
    conf_file_fields = random_conf_file()
    print "AddConfFile",
    conf_file_id = AddConfFile(admin, conf_file_fields)

    # Should return a unique conf_file_id
    assert conf_file_id not in conf_file_ids
    conf_file_ids.append(conf_file_id)
    print "=>", conf_file_id

    # Check configuration file
    print "GetConfFiles(%d)" % conf_file_id,
    conf_file = GetConfFiles(admin, [conf_file_id])[0]
    for field in conf_file_fields:
        assert unicmp(conf_file[field], conf_file_fields[field])
    print "=> OK"

    # Update configuration file
    conf_file_fields = random_conf_file()
    print "UpdateConfFile(%d)" % conf_file_id,
    UpdateConfFile(admin, conf_file_id, conf_file_fields)
    print "=> OK"

    # Check configuration file
    conf_file = GetConfFiles(admin, [conf_file_id])[0]
    for field in conf_file_fields:
        assert unicmp(conf_file[field], conf_file_fields[field])

    # Add to all node groups
    for nodegroup_id in nodegroup_ids:
        print "AddConfFileToNodeGroup(%d, %d)" % (conf_file_id, nodegroup_id),
        AddConfFileToNodeGroup(admin, conf_file_id, nodegroup_id)
        print "=> OK"

    # Add to all nodes
    for node_id in node_ids:
        print "AddConfFileToNode(%d, %d)" % (conf_file_id, node_id),
        AddConfFileToNode(admin, conf_file_id, node_id)
        print "=> OK"

print "GetConfFiles",
conf_files = GetConfFiles(admin, conf_file_ids)
assert set(conf_file_ids) == set([conf_file['conf_file_id'] for conf_file in conf_files])
for conf_file in conf_files:
    assert set(nodegroup_ids) == set(conf_file['nodegroup_ids'])
    assert set(node_ids) == set(conf_file['node_ids'])
print "=>", conf_file_ids

# Add slice attribute types
attribute_type_ids = []
for i in range(3):
    def random_attribute_type():
        return {
            'name': randstr(100),
            'description': randstr(254),
            'min_role_id': random.sample(roles.values(), 1)[0],
            }

    # Add slice attribute type
    attribute_type_fields = random_attribute_type()
    print "AddSliceAttributeType",
    attribute_type_id = AddSliceAttributeType(admin, attribute_type_fields)

    # Should return a unique attribute_type_id
    assert attribute_type_id not in attribute_type_ids
    attribute_type_ids.append(attribute_type_id)
    print "=>", attribute_type_id

    # Check slice attribute type
    print "GetSliceAttributeTypes(%d)" % attribute_type_id,
    attribute_type = GetSliceAttributeTypes(admin, [attribute_type_id])[0]
    for field in attribute_type_fields:
        assert unicmp(attribute_type[field], attribute_type_fields[field])
    print "=> OK"

    # Update slice attribute type
    attribute_type_fields = random_attribute_type()
    print "UpdateSliceAttributeType(%d)" % attribute_type_id,
    UpdateSliceAttributeType(admin, attribute_type_id, attribute_type_fields)
    print "=> OK"

    # Check slice attribute type again
    attribute_type = GetSliceAttributeTypes(admin, [attribute_type_id])[0]
    for field in attribute_type_fields:
        assert unicmp(attribute_type[field], attribute_type_fields[field])

# Add slices and slice attributes
slice_ids = []
slice_attribute_ids = []
for site in sites:
    for i in range(site['max_slices']):
        def random_slice():
            return {
                'name': site['login_base'] + "_" + randstr(11, letters).lower(),
                'url': "http://" + randhostname() + "/",
                'description': randstr(2048),
                }

        # Add slice
        slice_fields = random_slice()
        print "AddSlice",
        slice_id = AddSlice(admin, slice_fields)

        # Should return a unique slice_id
        assert slice_id not in slice_ids
        slice_ids.append(slice_id)
        print "=>", slice_id

        # Check slice
        print "GetSlices(%d)" % slice_id,
        slice = GetSlices(admin, [slice_id])[0]
        for field in slice_fields:
            assert unicmp(slice[field], slice_fields[field])
        print "=> OK"

        # Update slice
        slice_fields = random_slice()
        # Cannot change slice name
        del slice_fields['name']
        print "UpdateSlice(%d)" % slice_id,
        UpdateSlice(admin, slice_id, slice_fields)
        slice = GetSlices(admin, [slice_id])[0]
        for field in slice_fields:
            assert unicmp(slice[field], slice_fields[field])
        print "=> OK"

        # Add slice to all nodes
        print "AddSliceToNodes(%d, %s)" % (slice_id, str(node_ids)),
        AddSliceToNodes(admin, slice_id, node_ids)
        slice = GetSlices(admin, [slice_id])[0]
        assert set(node_ids) == set(slice['node_ids'])
        print "=> OK"

        # Add users to slice
        for person_id in person_ids:
            print "AddPersonToSlice(%d, %d)" % (person_id, slice_id),
            AddPersonToSlice(admin, person_id, slice_id)
            print "=> OK" 
        slice = GetSlices(admin, [slice_id])[0]
        assert set(person_ids) == set(slice['person_ids'])

        # Set slice/sliver attributes
        for attribute_type_id in attribute_type_ids:
            value = randstr(16, letters + '_' + digits)
            # Make it a sliver attribute with 50% probability
            node_id = random.sample(node_ids + [None] * len(node_ids), 1)[0]

            # Add slice attribute
            print "AddSliceAttribute(%d, %d)" % (slice_id, attribute_type_id),
            if node_id is None:
                slice_attribute_id = AddSliceAttribute(admin, slice_id, attribute_type_id, value)
            else:
                slice_attribute_id = AddSliceAttribute(admin, slice_id, attribute_type_id, value, node_id)

            # Should return a unique slice_attribute_id
            assert slice_attribute_id not in slice_attribute_ids
            slice_attribute_ids.append(slice_attribute_id)
            print "=>", slice_attribute_id

            # Check slice attribute
            print "GetSliceAttributes(%d)" % slice_attribute_id,
            slice_attribute = GetSliceAttributes(admin, [slice_attribute_id])[0]
            for field in 'attribute_type_id', 'slice_id', 'node_id', 'slice_attribute_id', 'value':
                assert unicmp(slice_attribute[field], locals()[field])
            print "=> OK"

            # Update slice attribute
            value = randstr(16, letters + '_' + digits)
            print "UpdateSliceAttribute(%d)" % slice_attribute_id,
            UpdateSliceAttribute(admin, slice_attribute_id, value)
            slice_attribute = GetSliceAttributes(admin, [slice_attribute_id])[0]
            for field in 'attribute_type_id', 'slice_id', 'node_id', 'slice_attribute_id', 'value':
                assert unicmp(slice_attribute[field], locals()[field])
            print "=> OK"

# Delete slices
for slice_id in slice_ids:
    # Delete slice attributes
    slice = GetSlices(admin, [slice_id])[0]
    for slice_attribute_id in slice['slice_attribute_ids']:
        print "DeleteSliceAttribute(%d, %d)" % (slice_id, slice_attribute_id),
        DeleteSliceAttribute(admin, slice_attribute_id)
        print "=> OK"
    slice = GetSlices(admin, [slice_id])[0]
    assert not slice['slice_attribute_ids']

    # Delete users from slice
    for person_id in person_ids:
        print "DeletePersonFromSlice(%d, %d)" % (person_id, slice_id),
        DeletePersonFromSlice(admin, person_id, slice_id)
        print "=> OK"
    slice = GetSlices(admin, [slice_id])[0]
    assert not slice['person_ids']

    # Delete nodes from slice
    print "DeleteSliceFromNodes(%d, %s)" % (slice_id, node_ids),
    DeleteSliceFromNodes(admin, slice_id, node_ids)
    print "=> OK"
    slice = GetSlices(admin, [slice_id])[0]
    assert not slice['node_ids']

    # Delete slice
    print "DeleteSlice(%d)" % slice_id,
    DeleteSlice(admin, slice_id)
    assert not GetSlices(admin, [slice_id])

    # Make sure it really deleted it
    slices = GetSlices(admin, slice_ids)
    assert slice_id not in [slice['slice_id'] for slice in slices]
    print "=> OK"

print "GetSlices",
assert not GetSlices(admin, slice_ids)
print "=> []"

# Delete slice attribute types
for attribute_type_id in attribute_type_ids:
    # Delete slice attribute type
    print "DeleteSliceAttributeType(%d)" % attribute_type_id,
    DeleteSliceAttributeType(admin, attribute_type_id)
    assert not GetSliceAttributeTypes(admin, [attribute_type_id])

    # Make sure it really deleted it
    attribute_types = GetSliceAttributeTypes(admin, attribute_type_ids)
    assert attribute_type_id not in [attribute_type['attribute_type_id'] for attribute_type in attribute_types]
    print "=> OK"

print "GetSliceAttributeTypes",
assert not GetSliceAttributeTypes(admin, attribute_type_ids)
print "=> []"

# Delete configuration files
for conf_file in conf_files:
    conf_file_id = conf_file['conf_file_id']

    for node_id in conf_file['node_ids']:
        print "DeleteConfFileFromNode(%d, %d)" % (conf_file_id, node_id),
        DeleteConfFileFromNode(admin, conf_file_id, node_id)
        print "=> OK"

    for nodegroup_id in conf_file['nodegroup_ids']:
        print "DeleteConfFileFromNodeGroup(%d, %d)" % (conf_file_id, nodegroup_id),
        DeleteConfFileFromNodeGroup(admin, conf_file_id, nodegroup_id)
        print "=> OK"

    print "DeleteConfFile(%d)" % conf_file_id,
    DeleteConfFile(admin, conf_file_id)
    print "=> OK"

print "GetConfFiles",
assert not GetConfFiles(admin, conf_file_ids)
print "=> []"

# Delete PCUs
for pcu in pcus:
    pcu_id = pcu['pcu_id']

    for node_id in pcu['node_ids']:
        print "DeleteNodeFromPCU(%d, %d)" % (node_id, pcu_id),
        DeleteNodeFromPCU(admin, node_id, pcu_id)
        print "=> OK"

    print "DeletePCU(%d)" % pcu_id,
    DeletePCU(admin, pcu_id)
    print "=> OK"

print "GetPCUs",
assert not GetPCUs(admin, pcu_ids)
print "=> []"
    
# Delete node networks
for nodenetwork_id in nodenetwork_ids:
    print "DeleteNodeNetwork(%d)" % nodenetwork_id,
    DeleteNodeNetwork(admin, nodenetwork_id)
    print "=>", "OK"

print "GetNodeNetworks",
assert not GetNodeNetworks(admin, nodenetwork_ids)
print "=> []"

# Delete nodes
for node_id in node_ids:
    # Remove from node groups
    for nodegroup_id in nodegroup_ids:
        print "DeleteNodeFromNodeGroup(%d, %d)" % (nodegroup_id, node_id),
        DeleteNodeFromNodeGroup(admin, nodegroup_id, node_id)
        print "=> OK"
    node = GetNodes(admin, [node_id])[0]
    assert not node['nodegroup_ids']

    # Delete node
    print "DeleteNode(%d)" % node_id,
    DeleteNode(admin, node_id)
    assert not GetNodes(admin, [node_id])

    # Make sure it really deleted it
    nodes = GetNodes(admin, node_ids)
    assert node_id not in [node['node_id'] for node in nodes]
    print "=> OK"

print "GetNodes",
assert not GetNodes(admin, node_ids)
print "=> []"

nodegroups = GetNodeGroups(admin, nodegroup_ids)
for nodegroup in nodegroups:
    assert not set(node_ids).intersection(nodegroup['node_ids'])

# Delete users
for person_id in person_ids:
    # Delete keys
    person = GetPersons(admin, [person_id])[0]
    for key_id in person['key_ids']:
        print "DeleteKey(%d)" % key_id,
        DeleteKey(admin, key_id)
        print "=> OK"
    person = GetPersons(admin, [person_id])[0]
    assert not person['key_ids']

    # Remove from each site
    for site_id in site_ids:
        print "DeletePersonFromSite(%d, %d)" % (person_id, site_id),
        DeletePersonFromSite(admin, person_id, site_id)
        print "=> OK"
    person = GetPersons(admin, [person_id])[0]
    assert not person['site_ids']

    # Revoke role
    person = GetPersons(admin, [person_id])[0]
    for role_id in person['role_ids']:
        print "DeleteRoleFromPerson(%d, %d)" % (role_id, person_id),
        DeleteRoleFromPerson(admin, role_id, person_id)
        print "=> OK"
    person = GetPersons(admin, [person_id])[0]
    assert not person['role_ids']

    # Disable account
    UpdatePerson(admin, person_id, {'enabled': False})
    person = GetPersons(admin, [person_id])[0]
    assert not person['enabled']

    # Delete account
    print "DeletePerson(%d)" % person_id,
    DeletePerson(admin, person_id)
    assert not GetPersons(admin, [person_id])                         
    print "=> OK"

print "GetPersons",
assert not GetPersons(admin, person_ids)
print "=> []"

# Delete node groups
for nodegroup_id in nodegroup_ids:
    print "DeleteNodeGroup(%d)" % nodegroup_id,
    DeleteNodeGroup(admin, nodegroup_id)
    assert not GetNodeGroups(admin, [nodegroup_id])
    print "=> OK"

print "GetNodeGroups",
assert not GetNodeGroups(admin, nodegroup_ids)
print "=> []"

# Delete site addresses
for address_id in address_ids:
    # Remove address types
    for address_type_id in address_type_ids:
        print "DeleteAddressTypeFromAddress(%d, %d)" % (address_type_id, address_id),
        DeleteAddressTypeFromAddress(admin, address_type_id, address_id)
        print "=> OK"
    address = GetAddresses(admin, [address_id])[0]
    assert not address['address_type_ids']

    print "DeleteAddress(%d)" % address_id,
    DeleteAddress(admin, address_id)
    assert not GetAddresses(admin, [address_id])
    print "=> OK"

print "GetAddresss",
assert not GetAddresses(admin, address_ids)
print "=> []"

# Delete address types
for address_type_id in address_type_ids:
    print "DeleteAddressType(%d)" % address_type_id,
    DeleteAddressType(admin, address_type_id)
    assert not GetAddressTypes(admin, [address_type_id])
    print "=> OK"
    
print "GetAddressTypes",
assert not GetAddressTypes(admin, address_type_ids)
print "=> []"

# Delete sites
for site_id in site_ids:
    print "DeleteSite(%d)" % site_id,
    DeleteSite(admin, site_id)
    assert not GetSites(admin, [site_id])
    print "=> OK"

print "GetSites",
assert not GetSites(admin, site_ids)
print "=> []"

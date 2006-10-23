#!/usr/bin/env ./Shell.py
#
# Test script example
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Test.py,v 1.10 2006/10/16 21:57:28 mlhuang Exp $
#

from pprint import pprint
from string import letters, digits, punctuation
import re
import socket
import struct

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

low_xml_chars  = map(unichr, [0x9, 0xA, 0xD])
low_xml_chars += map(unichr, xrange(0x20, 0x7F - 1))
low_xml_chars += map(unichr, xrange(0x84 + 1, 0x86 - 1))
low_xml_chars += map(unichr, xrange(0x9F + 1, 0xFF))
valid_xml_chars  = list(low_xml_chars)
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
    name = randstr(254)
    abbreviated_name = randstr(50)
    login_base = randstr(20, letters).lower()
    latitude = int(randfloat(-90.0, 90.0) * 1000) / 1000.0
    longitude = int(randfloat(-180.0, 180.0) * 1000) / 1000.0

    # Add site
    print "AddSite(%s)" % login_base,
    site_id = AddSite(admin, name, abbreviated_name, login_base,
                      {'latitude': latitude, 'longitude': longitude})

    # Should return a unique site_id
    assert site_id not in site_ids
    site_ids.append(site_id)
    print "=>", site_id

    # Check site
    print "GetSites(%d)" % site_id,
    site = GetSites(admin, [site_id])[0]
    for key in 'name', 'abbreviated_name', 'login_base', 'latitude', 'longitude', 'site_id':
        assert unicmp(site[key], locals()[key])
    print "=> OK"

    # Update site
    name = randstr(254)
    abbreviated_name = randstr(50)
    latitude = int(randfloat(-90.0, 90.0) * 1000) / 1000.0
    longitude = int(randfloat(-180.0, 180.0) * 1000) / 1000.0
    max_slices = 10
    print "UpdateSite(%s)" % login_base,
    UpdateSite(admin, site_id, {'name': name, 'abbreviated_name': abbreviated_name,
                                'latitude': latitude, 'longitude': longitude,
                                'max_slices': max_slices})
    site = GetSites(admin, [site_id])[0]
    for key in 'name', 'abbreviated_name', 'latitude', 'longitude', 'max_slices':
        assert unicmp(site[key], locals()[key])
    print "=> OK"

print "GetSites",
sites = GetSites(admin, site_ids)
assert set(site_ids) == set([site['site_id'] for site in sites])
print "=>", site_ids

print "GetRoles",
roles = GetRoles(admin)
role_ids = [role['role_id'] for role in roles]
roles = [role['name'] for role in roles]
roles = dict(zip(roles, role_ids))
print "=>", role_ids

# Add users
person_ids = []
for auth in user, pi, tech:
    first_name = randstr(128)
    last_name = randstr(128)
    # 119 + 1 + 64 + 64 + 6 = 254
    email = (randstr(119, letters + digits) + "@" + randhostname()).lower()
    bio = randstr(254)
    # Accounts are disabled by default
    enabled = False

    auth['Username'] = email
    auth['AuthString'] = randstr(254)

    # Add account
    print "AddPerson(%s)" % email,
    person_id = AddPerson(admin, first_name, last_name,
                          {'email': email, 'bio': bio,
                           'password': auth['AuthString']})

    # Should return a unique person_id
    assert person_id not in person_ids
    person_ids.append(person_id)
    print "=>", person_id

    # Check account
    print "GetPersons(%d)" % person_id,
    person = GetPersons(admin, [person_id])[0]
    for key in 'first_name', 'last_name', 'email', 'bio', 'person_id', 'enabled':
        assert unicmp(person[key], locals()[key])
    print "=> OK"

    # Update account
    first_name = randstr(128)
    last_name = randstr(128)
    bio = randstr(254)
    print "UpdatePerson(%d)" % person_id,
    UpdatePerson(admin, person_id, {'first_name': first_name,
                                    'last_name': last_name,
                                    'bio': bio})
    print "=> OK"

    # Check account again
    person = GetPersons(admin, [person_id])[0]
    for key in 'first_name', 'last_name', 'email', 'bio':
        assert unicmp(person[key], locals()[key])

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

print "GetPersons",
persons = GetPersons(admin, person_ids)
assert set(person_ids) == set([person['person_id'] for person in persons])
print "=>", person_ids

# Add node groups
nodegroup_ids = []
for i in range(3):
    name = randstr(50)
    description = randstr(200)

    # Add node group
    print "AddNodeGroup",
    nodegroup_id = AddNodeGroup(admin, name, {'description': description})

    # Should return a unique nodegroup_id
    assert nodegroup_id not in nodegroup_ids
    nodegroup_ids.append(nodegroup_id)
    print "=>", nodegroup_id

    # Check node group
    print "GetNodeGroups(%d)" % nodegroup_id,
    nodegroup = GetNodeGroups(admin, [nodegroup_id])[0]
    for key in 'name', 'description', 'nodegroup_id':
        assert unicmp(nodegroup[key], locals()[key])
    print "=> OK"

    # Update node group
    name = randstr(16, letters + ' ' + digits)
    description = randstr(200)
    print "UpdateNodeGroup",
    UpdateNodeGroup(admin, nodegroup_id, {'name': name, 'description': description})
    print "=> OK"

    # Check node group again
    nodegroup = GetNodeGroups(admin, [nodegroup_id])[0]
    for key in 'name', 'description', 'nodegroup_id':
        assert unicmp(nodegroup[key], locals()[key])

print "GetNodeGroups",
nodegroups = GetNodeGroups(admin, nodegroup_ids)
assert set(nodegroup_ids) == set([nodegroup['nodegroup_id'] for nodegroup in nodegroups])
print "=>", nodegroup_ids

# Add nodes
node_ids = []
for site_id in site_ids:
    for i in range(3):
        hostname = randhostname()
        boot_state = 'inst'
        model = randstr(255)

        # Add node
        print "AddNode(%s)" % hostname,
        node_id = AddNode(admin, site_id, hostname,
                          {'boot_state': boot_state, 'model': model})

        # Should return a unique node_id
        assert node_id not in node_ids
        node_ids.append(node_id)
        print "=>", node_id

        # Check node
        print "GetNodes(%d)" % node_id,
        node = GetNodes(admin, [node_id])[0]
        for key in 'hostname', 'boot_state', 'model', 'node_id':
            assert unicmp(node[key], locals()[key])
        print "=> OK"

        # Update node
        hostname = randhostname()
        model = randstr(255)
        print "UpdateNode(%d)" % node_id,
        UpdateNode(admin, node_id, {'hostname': hostname, 'model': model})
        print "=> OK"

        # Check node again
        node = GetNodes(admin, [node_id])[0]
        for key in 'hostname', 'boot_state', 'model', 'node_id':
            assert unicmp(node[key], locals()[key])

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

# Add node networks
nodenetwork_ids = []
for node_id in node_ids:
    ip = randint(0, 0xffffffff)
    netmask = (0xffffffff << randint(2, 31)) & 0xffffffff
    network = ip & netmask
    broadcast = ((ip & netmask) | ~netmask) & 0xffffffff
    gateway = randint(network + 1, broadcast - 1)
    dns1 = randint(0, 0xffffffff)
    bwlimit = randint(500000, 10000000)

    for method in 'static', 'dhcp':
        optional = {'bwlimit': bwlimit}
        if method == 'static':
            for key in 'ip', 'netmask', 'network', 'broadcast', 'gateway', 'dns1':
                optional[key] = socket.inet_ntoa(struct.pack('>L', locals()[key]))

        # Add node network
        print "AddNodeNetwork(%s)" % method,
        nodenetwork_id = AddNodeNetwork(admin, node_id, method, 'ipv4', optional)

        # Should return a unique nodenetwork_id
        assert nodenetwork_id not in nodenetwork_ids
        nodenetwork_ids.append(nodenetwork_id)
        print "=>", nodenetwork_id

        # Check node network
        print "GetNodeNetworks(%d)" % nodenetwork_id,
        nodenetwork = GetNodeNetworks(admin, [nodenetwork_id])[0]
        if method == 'static':
            for key in 'ip', 'netmask', 'network', 'broadcast', 'gateway', 'dns1':
                address = struct.unpack('>L', socket.inet_aton(nodenetwork[key]))[0]
                assert address == locals()[key]
        print "=> OK"

        # Update node network
        optional = {'bwlimit': bwlimit}
        if nodenetwork['method'] == 'static':
            for key in 'ip', 'netmask', 'network', 'broadcast', 'gateway', 'dns1':
                optional[key] = socket.inet_ntoa(struct.pack('>L', locals()[key]))

        print "UpdateNodeNetwork(%d)" % nodenetwork_id,
        UpdateNodeNetwork(admin, nodenetwork['nodenetwork_id'], optional)
        print "=> OK"

        # Check node network again
        nodenetwork = GetNodeNetworks(admin, [nodenetwork_id])[0]
        if nodenetwork['method'] == 'static':
            for key in 'ip', 'netmask', 'network', 'broadcast', 'gateway', 'dns1':
                address = struct.unpack('>L', socket.inet_aton(nodenetwork[key]))[0]
                assert address == locals()[key]

print "GetNodeNetworks",
nodenetworks = GetNodeNetworks(admin, nodenetwork_ids)
assert set(nodenetwork_ids) == set([nodenetwork['nodenetwork_id'] for nodenetwork in nodenetworks])
print "=>", nodenetwork_ids

# Add slice attribute types
attribute_type_ids = []
for i in range(3):
    name = randstr(100)
    description = randstr(254)
    min_role_id = random.sample(roles.values(), 1)[0]

    # Add slice attribute type
    print "AddSliceAttributeType",
    attribute_type_id = AddSliceAttributeType(admin, name,
                                         {'description': description,
                                          'min_role_id': min_role_id})

    # Should return a unique attribute_type_id
    assert attribute_type_id not in attribute_type_ids
    attribute_type_ids.append(attribute_type_id)
    print "=>", attribute_type_id

    # Check slice attribute type
    print "GetSliceAttributeTypes(%d)" % attribute_type_id,
    attribute_type = GetSliceAttributeTypes(admin, [attribute_type_id])[0]
    for key in 'name', 'min_role_id', 'description':
        assert unicmp(attribute_type[key], locals()[key])
    print "=> OK"

    # Update slice attribute type
    name = "attribute_" + randstr(10, letters + '_')
    description = randstr(254)
    min_role_id = random.sample(roles.values(), 1)[0]
    print "UpdateSliceAttributeType(%d)" % attribute_type_id,
    UpdateSliceAttributeType(admin, attribute_type_id,
                             {'name': name,
                              'description': description,
                              'min_role_id': min_role_id})
    attribute_type = GetSliceAttributeTypes(admin, [attribute_type_id])[0]
    for key in 'name', 'min_role_id', 'description':
        assert unicmp(attribute_type[key], locals()[key])
    print "=> OK"

# Add slices and slice attributes
slice_ids = []
slice_attribute_ids = []
for site in sites:
    for i in range(10):
        name = site['login_base'] + "_" + randstr(11, letters).lower()
        url = "http://" + randhostname() + "/"
        description = randstr(2048)

        # Add slice
        print "AddSlice(%s)" % name,
        slice_id = AddSlice(admin, name, {'url': url, 'description': description})

        # Should return a unique slice_id
        assert slice_id not in slice_ids
        slice_ids.append(slice_id)
        print "=>", slice_id

        # Check slice
        print "GetSlices(%d)" % slice_id,
        slice = GetSlices(admin, [slice_id])[0]
        for key in 'name', 'url', 'description', 'slice_id':
            assert unicmp(slice[key], locals()[key])
        print "=> OK"

        # Update slice
        url = "http://" + randhostname() + "/"
        description = randstr(2048)
        print "UpdateSlice(%d)" % slice_id,
        UpdateSlice(admin, slice_id, {'url': url, 'description': description})
        slice = GetSlices(admin, [slice_id])[0]
        for key in 'name', 'url', 'description', 'slice_id':
            assert unicmp(slice[key], locals()[key])
        print "=> OK"

        # Add slice to all nodes
        print "AddSliceToNodes(%d, %s)" % (slice_id, str(node_ids)),
        AddSliceToNodes(admin, name, node_ids)
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
            for key in 'attribute_type_id', 'slice_id', 'node_id', 'slice_attribute_id', 'value':
                assert unicmp(slice_attribute[key], locals()[key])
            print "=> OK"

            # Update slice attribute
            url = "http://" + randhostname() + "/"
            description = randstr(2048)
            print "UpdateSliceAttribute(%d)" % slice_attribute_id,
            UpdateSliceAttribute(admin, slice_attribute_id, value)
            slice_attribute = GetSliceAttributes(admin, [slice_attribute_id])[0]
            for key in 'attribute_type_id', 'slice_id', 'node_id', 'slice_attribute_id', 'value':
                assert unicmp(slice_attribute[key], locals()[key])
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

# Delete sites
for site_id in site_ids:
    print "DeleteSite(%d)" % site_id,
    DeleteSite(admin, site_id)
    assert not GetSites(admin, [site_id])
    print "=> OK"

print "GetSites",
assert not GetSites(admin, site_ids)
print "=> []"

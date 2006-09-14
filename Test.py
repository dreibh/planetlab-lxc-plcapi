#!/usr/bin/env ./Shell.py
#
# Test script example
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Test.py,v 1.4 2006/09/13 15:48:25 tmack Exp $
#

from pprint import pprint
from string import letters, digits, punctuation

from random import Random
random = Random()

import re

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
    print "AdmAddSite(%s)" % login_base,
    site_id = AdmAddSite(admin, name, abbreviated_name, login_base,
                         {'latitude': latitude, 'longitude': longitude})

    # Should return a unique site_id
    assert site_id not in site_ids
    site_ids.append(site_id)
    print "=>", site_id

    print "AdmGetSites(%d)" % site_id,
    site = AdmGetSites(admin, [site_id])[0]
    for key in 'name', 'abbreviated_name', 'login_base', 'latitude', 'longitude', 'site_id':
        assert unicmp(site[key], locals()[key])
    print "=> OK"

print "AdmGetSites",
sites = AdmGetSites(admin, site_ids)
assert set(site_ids) == set([site['site_id'] for site in sites])
print "=>", site_ids

print "AdmGetAllRoles",
role_ids = AdmGetAllRoles(admin)
roles = dict(zip(role_ids.values(), map(int, role_ids.keys())))
print "=>", role_ids

# Add users
person_ids = []
for auth in user, pi, tech:
    first_name = randstr(128)
    last_name = randstr(128)
    email = randstr(119, letters + digits) + "@" + randhostname()
    bio = randstr(254)
    # Accounts are disabled by default
    enabled = False

    auth['Username'] = email
    auth['AuthString'] = randstr(254)

    print "AdmAddPerson(%s)" % email,
    person_id = AdmAddPerson(admin, first_name, last_name,
                             {'email': email, 'bio': bio,
                              'password': auth['AuthString']})

    # Should return a unique person_id
    assert person_id not in person_ids
    person_ids.append(person_id)
    print "=>", person_id

    # Check account
    print "AdmGetPersons(%d)" % person_id,
    person = AdmGetPersons(admin, [person_id])[0]
    for key in 'first_name', 'last_name', 'bio', 'person_id', 'enabled':
        assert unicmp(person[key], locals()[key])
    print "=> OK"

    # Enable account
    print "AdmSetPersonEnabled(%d, True)" % person_id,
    AdmSetPersonEnabled(admin, person_id, True)
    person = AdmGetPersons(admin, [person_id])[0]
    assert person['enabled']
    print "=> OK"

    # Add role
    role_id = roles[auth['Role']]
    print "AdmGrantRoleToPerson(%d, %d)" % (person_id, role_id),
    AdmGrantRoleToPerson(admin, person_id, role_id)
    print "=> OK"

    print "AdmGetPersonRoles(%d)" % person_id,
    person_roles = AdmGetPersonRoles(admin, person_id)
    person_role_ids = map(int, person_roles.keys())
    assert [role_id] == person_role_ids
    person = AdmGetPersons(admin, [person_id])[0]
    assert [role_id] == person['role_ids']
    print "=>", person_role_ids

    # Associate account with each site
    for site_id in site_ids:
        print "AdmAddPersonToSite(%d, %d)" % (person_id, site_id),
        AdmAddPersonToSite(admin, person_id, site_id)
        print "=> OK"

    # Make sure it really did it
    print "AdmGetPersonSites(%d)" % person_id,
    person_site_ids = AdmGetPersonSites(auth, person_id)
    assert set(site_ids) == set(person_site_ids)
    person = AdmGetPersons(admin, [person_id])[0]
    assert set(site_ids) == set(person['site_ids'])
    print "=>", person_site_ids

    # First site should be the primary site
    print "AdmSetPersonPrimarySite(%d, %d)" % (person_id, person_site_ids[1]),
    AdmSetPersonPrimarySite(auth, person_id, person_site_ids[1])
    assert AdmGetPersonSites(auth, person_id)[0] == person_site_ids[1]
    person = AdmGetPersons(admin, [person_id])[0]
    assert person['site_ids'][0] == person_site_ids[1]
    print "=> OK"

print "AdmGetPersons",
persons = AdmGetPersons(admin, person_ids)
assert set(person_ids) == set([person['person_id'] for person in persons])
print "=>", person_ids

# Add nodes
node_ids = []
for site_id in site_ids:
    for i in range(3):
        hostname = randhostname()
        boot_state = 'inst'
        model = randstr(255)

        # Add node
        print "AdmAddNode(%s)" % hostname,
        node_id = AdmAddNode(admin, site_id, hostname, boot_state,
                             {'model': model})

        # Should return a unique node_id
        assert node_id not in node_ids
        node_ids.append(node_id)
        print "=>", node_id

        # Check node
        print "AdmGetNodes(%d)" % node_id,
        node = AdmGetNodes(admin, [node_id])[0]
        for key in 'hostname', 'boot_state', 'model', 'node_id':
            assert unicmp(node[key], locals()[key])
        print "=> OK"

    # XXX AdmGetSiteNodes

# Add Node Group
node_group_name = 'tng'
node_group_description = 'test node group' 
print "AdmAddNodeGroup(admin, %s, %s)" % (node_group_name, node_group_description),
node_group_id = AdmAddNodeGroup(admin, node_group_name, node_group_description)
print "=>", node_group_id

# Update Node Groupi
node_group_name = node_group_name + randstr(5)
node_group_description = node_group_description + randstr(5)
print "AdmUpdateNodeGroup(admin, %d, %s, %s)" % (node_group_id, node_group_name,node_group_description ),
assert AdmUpdateNodeGroup(admin, node_group_id, node_group_name, node_group_description)
print "=> OK"


# Get Node Groups
print "AdmGetNodeGroups(admin, %d)" % node_group_id,
assert AdmGetNodeGroups(admin, [node_group_id])
print "=> ", AdmGetNodeGroups(admin, [node_group_id])

# Add node to node group
new_node_id = AdmAddNode(admin, 1, randhostname(), 'inst')
print "AdmAddNodeToNodeGroup(admin, %d, %d)" % (node_group_id, new_node_id),
assert AdmAddNodeToNodeGroup(admin, node_group_id, new_node_id)
print "=> OK"

# Get Node Group Nodes
print "AdmGetNodeGroupNodes(admin, %s)" % node_group_id,
assert isinstance(AdmGetNodeGroupNodes(admin, node_group_id), list)
print "=>", AdmGetNodeGroupNodes(admin, node_group_id)

# Remove node from node group
print "AdmRemoveNodeFromNodeGroup(admin, %d, %d)" % (node_group_id, new_node_id),
assert AdmRemoveNodeFromNodeGroup(admin, node_group_id, new_node_id)
print "=> OK"
AdmDeleteNode(admin, new_node_id)

# Delete Node Group
print "AdmDeleteNodeGroup(%d)" % node_group_id, 
assert AdmDeleteNodeGroup(admin, node_group_id)
print "=> OK"


#Get Nodes
print "AdmGetNodes",
nodes = AdmGetNodes(admin, node_ids)
assert set(node_ids) == set([node['node_id'] for node in nodes])
print "=>", node_ids


#Get Site Nodes
for site_id in site_ids:
	print "AdmGetSiteNodes([%d])" % site_id,
	assert AdmGetSiteNodes(admin, [site_id])
	print "=> " , AdmGetSiteNodes(admin, [site_id])

print "AdmGetSiteNodes(%s)" % site_ids,
assert AdmGetSiteNodes(admin, site_ids)
print "=> ", AdmGetSiteNodes(admin, site_ids)


# Delete nodes
for node_id in node_ids:
    print "AdmDeleteNode(%d)" % node_id,
    AdmDeleteNode(admin, node_id)
    assert not AdmGetNodes(admin, [node_id])

    # Make sure it really deleted it
    nodes = AdmGetNodes(admin, node_ids)
    assert node_id not in [node['node_id'] for node in nodes]
    print "=> OK"

print "AdmGetNodes",
assert not AdmGetNodes(admin, node_ids)
print "=> []"

# Delete users
for person_id in person_ids:
    # Remove from each site
    for site_id in site_ids:
        print "AdmRemovePersonFromSite(%d, %d)" % (person_id, site_id),
        AdmRemovePersonFromSite(admin, person_id, site_id)
        assert site_id not in AdmGetPersonSites(admin, person_id)
        person = AdmGetPersons(admin, [person_id])[0]
        assert site_id not in person['site_ids']
        print "=> OK"

    assert not AdmGetPersonSites(admin, person_id)

    # Revoke role
    person_roles = AdmGetPersonRoles(admin, person_id)
    role_id = int(person_roles.keys()[0])
    print "AdmRevokeRoleFromPerson(%d, %d)" % (person_id, role_id),
    AdmRevokeRoleFromPerson(admin, person_id, role_id)
    assert not AdmGetPersonRoles(admin, person_id)
    person = AdmGetPersons(admin, [person_id])[0]
    assert not person['role_ids']
    print "=> OK"

    # Disable account
    print "AdmSetPersonEnabled(%d, False)" % person_id,
    AdmSetPersonEnabled(admin, person_id, False)
    person = AdmGetPersons(admin, [person_id])[0]
    assert not person['enabled']
    print "=> OK"

    # Delete account
    print "AdmDeletePerson(%d)" % person_id,
    AdmDeletePerson(admin, person_id)
    assert not AdmGetPersons(admin, [person_id])                         
    print "=> OK"

print "AdmGetPersons",
assert not AdmGetPersons(admin, person_ids)
print "=> []"

# Delete sites
for site_id in site_ids:
    print "AdmDeleteSite(%d)" % site_id,
    AdmDeleteSite(admin, site_id)
    assert not AdmGetSites(admin, [site_id])
    print "=> OK"

print "AdmGetSites",
assert not AdmGetSites(admin, site_ids)
print "=> []"


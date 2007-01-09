#!/usr/bin/python
#
# Test script example
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Test.py,v 1.15 2006/10/30 16:38:33 mlhuang Exp $
#

from pprint import pprint
from string import letters, digits, punctuation
from traceback import print_exc
from optparse import OptionParser
import base64
import os

from random import Random
random = Random()

from PLC.Shell import Shell
shell = Shell(globals())

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

def random_site():
    return {
        'name': randstr(254),
        'abbreviated_name': randstr(50),
        'login_base': randstr(20, letters).lower(),
        'latitude': int(randfloat(-90.0, 90.0) * 1000) / 1000.0,
        'longitude': int(randfloat(-180.0, 180.0) * 1000) / 1000.0,
        }
            
def random_address_type():
    return {
        'name': randstr(20),
        'description': randstr(254),
        }

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

def random_person():
    return {
        'first_name': randstr(128),
        'last_name': randstr(128),
        'email': randemail(),
        'bio': randstr(254),
        # Accounts are disabled by default
        'enabled': False,
        'password': randstr(254),
        }

def random_key():
    return {
        'key_type': random.sample(key_types, 1)[0],
        'key': randkey()
        }

def random_slice():
    return {
        'name': site['login_base'] + "_" + randstr(11, letters).lower(),
        'url': "http://" + randhostname() + "/",
        'description': randstr(2048),
        }

class Test:
    def __init__(self, check = True, verbose = True):
        self.check = check
        self.verbose = verbose
        
        self.site_ids = []
        self.address_type_ids = []
        self.address_ids = []
        self.person_ids = []

    def run(self,
            sites = 100,
            address_types = 3,
            addresses = 2,
            persons = 1000,
            keys = 3):
        try:
            try:
                self.AddSites(sites)
                self.AddAddressTypes(address_types)
                self.AddAddresses(addresses)
                self.AddPersons(persons)
            except:
                print_exc()
        finally:
            self.cleanup()

    def cleanup(self):
        self.DeletePersons()
        self.DeleteAddresses()
        self.DeleteAddressTypes()
        self.DeleteSites()

    def AddSites(self, n = 3):
        """
        Add a number of random sites.
        """

        for i in range(n):
            # Add site
            site_fields = random_site()
            site_id = AddSite(site_fields)

            # Should return a unique site_id
            assert site_id not in self.site_ids
            self.site_ids.append(site_id)

            if self.check:
                # Check site
                site = GetSites([site_id])[0]
                for field in site_fields:
                    assert site[field] == site_fields[field]

            # Update site
            site_fields = random_site()
            # XXX Currently cannot change login_base
            del site_fields['login_base']
            site_fields['max_slices'] = randint(1, 10)
            UpdateSite(site_id, site_fields)

            if self.check:
                # Check site again
                site = GetSites([site_id])[0]
                for field in site_fields:
                    assert site[field] == site_fields[field]

        if self.check:
            sites = GetSites(self.site_ids)
            assert set(self.site_ids) == set([site['site_id'] for site in sites])

        if self.verbose:
            print "Added sites", self.site_ids

    def DeleteSites(self):
        """
        Delete any random sites we may have added.
        """

        for site_id in self.site_ids:
            DeleteSite(site_id)
            if self.check:
                assert not GetSites([site_id])

        if self.check:
            assert not GetSites(self.site_ids)

        if self.verbose:
            print "Deleted sites", self.site_ids

        self.site_ids = []

    def AddAddressTypes(self, n = 3):
        """
        Add a number of random address types.
        """
        
        for i in range(n):
            address_type_fields = random_address_type()
            address_type_id = AddAddressType(address_type_fields)

            # Should return a unique address_type_id
            assert address_type_id not in self.address_type_ids
            self.address_type_ids.append(address_type_id)

            if self.check:
                # Check address type
                address_type = GetAddressTypes([address_type_id])[0]
                for field in 'name', 'description':
                    assert address_type[field] == address_type_fields[field]

                # Update address type
                address_type_fields = random_address_type()
                UpdateAddressType(address_type_id, address_type_fields)
            
                # Check address type again
                address_type = GetAddressTypes([address_type_id])[0]
                for field in 'name', 'description':
                    assert address_type[field] == address_type_fields[field]

        if self.check:
            address_types = GetAddressTypes(self.address_type_ids)
            assert set(self.address_type_ids) == set([address_type['address_type_id'] for address_type in address_types])

        if self.verbose:
            print "Added address types", self.address_type_ids

    def DeleteAddressTypes(self):
        """
        Delete any random address types we may have added.
        """

        for address_type_id in self.address_type_ids:
            DeleteAddressType(address_type_id)
            if self.check:
                assert not GetAddressTypes([address_type_id])

        if self.check:
            assert not GetAddressTypes(self.address_type_ids)

        if self.verbose:
            print "Deleted address types", self.address_type_ids

        self.address_type_ids = []

    def AddAddresses(self, n = 3):
        """
        Add a number of random addresses to each site.
        """

        for site_id in self.site_ids:
            for i in range(n):
                address_fields = random_address()
                address_id = AddSiteAddress(site_id, address_fields)

                # Should return a unique address_id
                assert address_id not in self.address_ids
                self.address_ids.append(address_id)

                if self.check:
                    # Check address
                    address = GetAddresses([address_id])[0]
                    for field in address_fields:
                        assert address[field] == address_fields[field]

                    # Update address
                    address_fields = random_address()
                    UpdateAddress(address_id, address_fields)

                    # Check address again
                    address = GetAddresses([address_id])[0]
                    for field in address_fields:
                        assert address[field] == address_fields[field]

                # Add address types
                for address_type_id in self.address_type_ids:
                    AddAddressTypeToAddress(address_type_id, address_id)

        if self.check:
            addresses = GetAddresses(self.address_ids)
            assert set(self.address_ids) == set([address['address_id'] for address in addresses])
            for address in addresses:
                assert set(self.address_type_ids) == set(address['address_type_ids'])

        if self.verbose:
            print "Added addresses", self.address_ids

    def DeleteAddresses(self):
        """
        Delete any random addresses we may have added.
        """

        # Delete site addresses
        for address_id in self.address_ids:
            # Remove address types
            for address_type_id in self.address_type_ids:
                DeleteAddressTypeFromAddress(address_type_id, address_id)

            if self.check:
                address = GetAddresses([address_id])[0]
                assert not address['address_type_ids']

            DeleteAddress(address_id)
            if self.check:
                assert not GetAddresses([address_id])

        if self.check:
            assert not GetAddresses(self.address_ids)

        if self.verbose:
            print "Deleted addresses", self.address_ids

        self.address_ids = []

    def AddPersons(self, n = 3):
        """
        Add a number of random users to each site.
        """

        roles = GetRoles()
        role_ids = [role['role_id'] for role in roles]
        roles = [role['name'] for role in roles]
        roles = dict(zip(roles, role_ids))

        for i in range(n):

            # Add account
            person_fields = random_person()
            person_id = AddPerson(person_fields)

            # Should return a unique person_id
            assert person_id not in self.person_ids
            self.person_ids.append(person_id)

            if self.check:
                # Check account
                person = GetPersons([person_id])[0]
                for field in person_fields:
                    if field != 'password':
                        assert person[field] == person_fields[field]

                # Update account
                person_fields = random_person()
                UpdatePerson(person_id, person_fields)

                # Check account again
                person = GetPersons([person_id])[0]
                for field in person_fields:
                    if field != 'password':
                        assert person[field] == person_fields[field]

            auth = {'AuthMethod': "password",
                    'Username': person_fields['email'],
                    'AuthString': person_fields['password']}

            if self.check:
                # Check that account is disabled
                try:
                    assert not AuthCheck(auth)
                except:
                    pass

            # Add random set of roles
            person_roles = random.sample(['user', 'pi', 'tech'], randint(1, 3))
            for person_role in person_roles:
                role_id = roles[person_role]
                AddRoleToPerson(role_id, person_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert set(person_roles) == set(person['roles'])

            # Enable account
            UpdatePerson(person_id, {'enabled': True})

            if self.check:
                # Check that account is enabled
                assert AuthCheck(auth)

            # Associate account with random set of sites
            person_site_ids = []
            for site_id in random.sample(self.site_ids, randint(1, len(self.site_ids))):
                AddPersonToSite(person_id, site_id)
                person_site_ids.append(site_id)

            if self.check:
                # Make sure it really did it
                person = GetPersons([person_id])[0]
                assert set(person_site_ids) == set(person['site_ids'])

            # Set a primary site
            primary_site_id = random.sample(person_site_ids, randint(1, len(person_site_ids)))[0]
            SetPersonPrimarySite(person_id, primary_site_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert person['site_ids'][0] == primary_site_id

        if self.verbose:
            print "Added users", self.person_ids

    def DeletePersons(self):
        # Delete users
        for person_id in self.person_ids:
            # Remove from each site
            for site_id in self.site_ids:
                DeletePersonFromSite(person_id, site_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert not person['site_ids']

            # Revoke roles
            person = GetPersons([person_id])[0]
            for role_id in person['role_ids']:
                DeleteRoleFromPerson(role_id, person_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert not person['role_ids']

            # Disable account
            UpdatePerson(person_id, {'enabled': False})

            if self.check:
                person = GetPersons([person_id])[0]
                assert not person['enabled']

            # Delete account
            DeletePerson(person_id)

            if self.check:
                assert not GetPersons([person_id])                         

        if self.check:
            assert not GetPersons(self.person_ids)

        if self.verbose:
            print "Deleted users", self.person_ids

        self.person_ids = []

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-c", "--check", action = "store_true", default = False, help = "Verify actions (default: %default)")
    parser.add_option("-q", "--quiet", action = "store_true", default = False, help = "Be quiet (default: %default)")
    parser.add_option("-p", "--populate", action = "store_true", default = False, help = "Do not cleanup (default: %default)")
    (options, args) = parser.parse_args()
    test = Test(check = options.check, verbose = not options.quiet)
    test.run()
    if not options.populate:
        test.cleanup()

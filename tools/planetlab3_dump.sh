#!/bin/bash
#
# Dumps the planetlab3 database on zulu, fixing a few things on the way
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2007 The Trustees of Princeton University
#
# $Id$
#

tables=(
node_bootstates
nodes
nodenetworks
node_nodenetworks
nodegroups
nodegroup_nodes
override_bootscripts
pod_hash
conf_file
conf_assoc
address_types
addresses
organizations
sites
roles
capabilities
persons
person_roles
person_capabilities
person_address
key_types
keys
person_keys
person_site
node_root_access
authorized_subnets
site_authorized_subnets
event_classes
dslice03_states
dslice03_attributetypes
dslice03_slices
dslice03_attributes
dslice03_sliceattribute
dslice03_slicenode
dslice03_sliceuser
dslice03_siteinfo
pcu
pcu_ports
join_request
whatsnew
node_hostnames
blacklist
dslice03_initscripts
dslice03_defaultattribute
peered_mas
sessions
)

# Dump tables
for table in "${tables[@]}" ; do
    pg_dump -U postgres -t $table planetlab3
done |

# Do some manual cleanup
sed -f <(cat <<EOF
# Swap person_id=1 (kfall@cs.berkeley.edu) with person_id=1303 (maint@planet-lab.org)
/^COPY \(persons\|person_roles\|person_capabilities\|person_address\|person_keys\|person_site\|node_root_access\)/,/^\\\./{
s/^1\t/1303\t/
t
s/^1303\t/1\t/
t
}
/^COPY dslice03_sliceuser/,/^\\\./{
s/\t1$/\t1303/
t
s/\t1303$/\t1/
t
}

# Swap person_id=2 (nakao@cs.princeton.edu) with person_id=13342 (root@planet-lab.org)
/^COPY \(persons\|person_roles\|person_capabilities\|person_address\|person_keys\|person_site\|node_root_access\)/,/^\\\./{
s/^2\t/13342\t/
t
s/^13342\t/2\t/
t
}
/^COPY dslice03_sliceuser/,/^\\\./{
s/\t2$/\t13342/
t
s/\t13342$/\t2/
t
}

# Swap site_id=1 (gt) with site_id=90 (pl)
/^COPY \(sites\|site_authorized_subnets\|dslice03_siteinfo\)/,/^\\\./{
s/^1\t/90\t/
t
s/^90\t/1\t/
t
}
/^COPY \(person_site\|pcu\)/,/^\\\./{
s/\([^\t]*\t\)1\t/\190\t/
t
s/\([^\t]*\t\)90\t/\11\t/
t
}
/^COPY \(dslice03_slices\)/,/^\\\./{
s/\([^\t]*\t[^\t]*\t\)1\t/\190\t/
t
s/\([^\t]*\t[^\t]*\t\)90\t/\11\t/
t
}
EOF
)

# Dump events and api_log schema only
pg_dump -U postgres -s -t events planetlab3
pg_dump -U postgres -s -t api_log planetlab3

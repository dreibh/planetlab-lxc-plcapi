#!/usr/bin/env /usr/bin/plcsh
#
# Convert old planetlab3 slice attributes and initscripts to new
# planetlab4 ones.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: slice_attributes.py,v 1.2 2007/02/03 00:43:37 mlhuang Exp $
#

import re
import base64

# Convert nm_net_{exempt_,}{min,max}_rate (bps) to
# net_{i2_,}{min,max}_rate and net_{i2_,}{min,max}_rate (kbps)
rename = {'nm_net_min_rate': 'net_min_rate',
          'nm_net_max_rate': 'net_max_rate',
          'nm_net_exempt_min_rate': 'net_i2_min_rate',
          'nm_net_exempt_max_rate': 'net_i2_max_rate'}
for slice_attribute in GetSliceAttributes({'name': rename.keys()}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Convert bps to kbps
    bps = int(slice_attribute['value'])
    kbps = bps / 1000

    # Add the new attribute
    if GetSlices([slice_id]):
        AddSliceAttribute(slice_id, rename[name], str(kbps))

    # Delete the old attribute
    DeleteSliceAttribute(id)

# Convert nm_net_{exempt_,}avg_rate to
# net_{i2_,}max_kbyte and net_{i2_,}thresh_kbyte
rename = {'nm_net_avg_rate': {'max': 'net_max_kbyte',
                              'thresh': 'net_thresh_kbyte'},
          'nm_net_exempt_avg_rate': {'max': 'net_i2_max_kbyte',
                                     'thresh': 'net_i2_thresh_kbyte'}}
for slice_attribute in GetSliceAttributes({'name': rename.keys()}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Convert bps to 80% and 100% of max bytes per day
    bps = int(slice_attribute['value'])
    max_kbyte = bps * 24 * 60 * 60 / 8 / 1000
    thresh_kbyte = int(0.8 * max_kbyte)

    # Add the new attribute
    if GetSlices([slice_id]):
        AddSliceAttribute(slice_id, rename[name]['max'], str(max_kbyte))
        AddSliceAttribute(slice_id, rename[name]['thresh'], str(thresh_kbyte))

    # Delete the old attribute
    DeleteSliceAttribute(id)

# Convert plc_slice_state
for slice_attribute in GetSliceAttributes({'name': 'plc_slice_state'}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Add the new attribute
    if GetSlices([slice_id]):
        if slice_attribute['value'] == "suspended":
            AddSliceAttribute(slice_id, 'enabled', "0")
        else:
            AddSliceAttribute(slice_id, 'enabled', "1")

    # Delete the old attribute
    DeleteSliceAttribute(id)
    
# Straight renames
rename = {'nm_cpu_share': 'cpu_share',
          'nm_disk_quota': 'disk_max',
          'nm_net_share': 'net_share',
          'nm_net_exempt_share': 'net_i2_share',
          'nm_net_max_byte': 'net_max_kbyte',
          'nm_net_max_thresh_byte': 'net_thresh_kbyte',
          'nm_net_max_exempt_byte': 'net_i2_max_kbyte',
          'nm_net_max_thresh_exempt_byte': 'net_i2_thresh_kbyte'}
for slice_attribute in GetSliceAttributes({'name': rename.keys()}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Pass straight through
    value = slice_attribute['value']

    # Add the new attribute
    if GetSlices([slice_id]):
        AddSliceAttribute(slice_id, rename[name], value)

    # Delete the old attribute
    DeleteSliceAttribute(id)

# Delete _deleted and deprecated slice attributes and types
for attribute_type in GetSliceAttributeTypes():
    id = attribute_type['attribute_type_id']
    name = attribute_type['name']

    if name == 'general_prop_share' or \
       re.match('nm_', name) or \
       re.search('_deleted$', name):
        DeleteSliceAttributeType(id)
        # N.B. Automatically deletes all slice attributes of this type

# Add Proper ops
proper_ops = [
    # give Stork permission to mount and unmount client dirs
    ('arizona_stork', 'mount_dir'),
    ('arizona_stork', 'set_file_flags pass, "1"'),
    ('arizona_stork', 'set_file_flags_list "1"'),
    ('arizona_stork', 'bind_socket sockname=64?:*'),
    ('arizona_stork2', 'mount_dir'),
    ('arizona_stork2', 'set_file_flags pass, "1"'),
    ('arizona_stork2', 'set_file_flags_list "1"'),
    ('arizona_stork2', 'bind_socket sockname=64?:*'),

    # give CoMon the necessary permissions to run slicestat
    ('princeton_slicestat', 'exec "root", pass, "/usr/local/planetlab/bin/pl-ps", none'),
    ('princeton_slicestat', 'exec "root", pass, "/usr/sbin/vtop", "bn1", none'),
    ('princeton_slicestat', 'open_file file=/proc/virtual/*/cacct'),
    ('princeton_slicestat', 'open_file file=/proc/virtual/*/limit'),
    ('princeton_comon', 'open_file file=/var/log/secure'),
    ('princeton_comon', 'exec "root", pass, "/bin/df", "/vservers", none'),

    # give pl_slicedir access to /etc/passwd
    ('pl_slicedir', 'open_file pass, "/etc/passwd"'),

    # nyu_d are building a DNS demux so give them access to port 53
    ('nyu_d', 'bind_socket'),
    ('nyu_oasis', 'bind_socket'),

    # QA slices need to be able to create and delete bind-mounts
    ('pl_qa_0', 'mount_dir'),
    ('pl_qa_1', 'mount_dir'),

    # irb_snort needs packet sockets for tcpdump
    ('irb_snort', 'create_socket'),

    # uw_ankur is using netlink sockets to do the same thing as netflow
    ('uw_ankur', 'create_socket'),

    # cornell_codons gets access to port 53 for now
    ('cornell_codons', 'create_socket'),

    # give Mic Bowman's conf-monitor service read-only access to root fs
    # and the ability to run df
    ('idsl_monitor', 'mount_dir "root:/", pass, "ro"'),
    ('idsl_monitor', 'unmount'),
    ('idsl_monitor', 'exec "root", pass, "/bin/df", "-P", "/", "/vservers", none'),

    # give Shark access to port 111 to run portmap
    # and port 955 to run mount
    ('nyu_shkr', 'bind_socket'),
    ('nyu_shkr', 'mount_dir "nfs:**:**"'),
    ('nyu_shkr', 'exec "root", pass, "/bin/umount", "-l", "/vservers/nyu_shkr/**", none'),

    # give tsinghua_lgh access to restricted ports
    ('tsinghua_lgh', 'bind_socket'),

    # CoDeeN needs port 53 too
    ('princeton_codeen', 'bind_socket sockname=53:*'),

    # give ucin_load access to /var/log/wtmp
    ('ucin_load', 'open_file file=/var/log/wtmp*'),

    # give google_highground permission to bind port 81 (and raw sockets)
    ('google_highground', 'bind_socket'),

    # pl_conf needs access to port 814
    ('pl_conf', 'bind_socket sockname=814:*'),
    ('pl_conf', 'open file=/home/*/.ssh/authorized_keys'),

    # give princeton_visp permission to read all packets sent through the
    # tap0 device
    ('princeton_visp', 'open file=/dev/net/tun, flags=rw'),

    # The PLB group needs the BGP port
    ('princeton_iias', 'bind_socket sockname=179:*'),
    ('princeton_visp', 'bind_socket sockname=179:*'),
    ('mit_rcp', 'bind_socket sockname=179:*'),
    ('princeton_bgpmux', 'bind_socket sockname=179:*'),
    ('princeton_bgpmux2', 'bind_socket sockname=179:*'),

    # PL-VINI group
    ('mit_rcp', 'exec "root", pass, "/usr/bin/chrt"'),
    ('princeton_iias', 'exec "root", pass, "/usr/bin/chrt"'),

    # Tycoon needs access to /etc/passwd to determine Slicename->XID mappings
    ('hplabs_tycoon_aucd', 'open_file file=/etc/passwd'),
]

for slice, op in proper_ops:
    try:
        AddSliceAttribute(slice, 'proper_op', op)
    except Exception, err:
        print "Warning: %s:" % slice, err

initscripts = dict([(initscript['initscript_id'], initscript) for initscript in [{'initscript_id': 8, 'script': 'IyEgL2Jpbi9zaA0KDQojIDxQcm9ncmFtIE5hbWU+DQojICAgIGJpbmRzY3JpcHQNCiMNCiMgPEF1dGhvcj4NCiMgICAgSmVmZnJ5IEpvaG5zdG9uIGFuZCBKZXJlbXkgUGxpY2h0YQ0KIw0KIyA8UHVycG9zZT4NCiMgICAgRG93bmxvYWRzIGFuZCBpbnN0YWxscyBzdG9yayBvbiBhIG5vZGUuDQoNCiMgc2F2ZSBvcmlnaW5hbCBQV0QNCk9MRFBXRD0kUFdEDQoNCiMgZXJyb3IgcmVwb3J0aW5nIGZ1bmN0aW9uDQplcnJvcigpDQp7DQogICBlY2hvDQogICBlY2hvICJQbGVhc2UgRS1tYWlsIHN0b3JrLXN1cHBvcnRAY3MuYXJpem9uYS5lZHUgaWYgeW91IGJlbGlldmUgeW91IGhhdmUiIA0KICAgZWNobyAicmVjZWl2ZWQgdGhpcyBtZXNzYWdlIGluIGVycm9yLiINCg0KICAgIyBnZXQgcmlkIG9mIENFUlQgZmlsZQ0KICAgaWYgWyAtZiAkQ0VSVCBdDQogICB0aGVuDQogICAgICBybSAtZiAkQ0VSVCA+IC9kZXYvbnVsbA0KICAgZmkNCg0KICAgIyByZXN0b3JlIG9yaWdpbmFsIFBXRA0KICAgY2QgJE9MRFBXRA0KICAgZXhpdCAxDQp9DQoNCkNFUlQ9YHB3ZGAvdGVtcGNydGZpbGUNCg0KI2Z1bmN0aW9ucw0KDQojIyMNCiMjIyBjcmVhdGVDZXJ0aWZpY2F0ZSgpDQojIyMgICAgcHJpbnRzIG91dCB0aGUgZXF1aWZheCBjZXJ0aWZpY2F0ZSB0byB1c2UgYW5kIHN0b3Jlcw0KIyMjICAgIHRoZSBmaWxlIG5hbWUgaW4gJENFUlQNCiMjIw0KZnVuY3Rpb24gY3JlYXRlQ2VydGlmaWNhdGUoKXsNCmNhdCA+ICRDRVJUIDw8RVFVSUZBWA0KLS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tDQpNSUlDa0RDQ0FmbWdBd0lCQWdJQkFUQU5CZ2txaGtpRzl3MEJBUVFGQURCYU1Rc3dDUVlEVlFRR0V3SlYNClV6RWNNQm9HQTFVRUNoTVRSWEYxYVdaaGVDQlRaV04xY21VZ1NXNWpMakV0TUNzR0ExVUVBeE1rUlhGMQ0KYVdaaGVDQlRaV04xY21VZ1IyeHZZbUZzSUdWQ2RYTnBibVZ6Y3lCRFFTMHhNQjRYRFRrNU1EWXlNVEEwDQpNREF3TUZvWERUSXdNRFl5TVRBME1EQXdNRm93V2pFTE1Ba0dBMVVFQmhNQ1ZWTXhIREFhQmdOVkJBb1QNCkUwVnhkV2xtWVhnZ1UyVmpkWEpsSUVsdVl5NHhMVEFyQmdOVkJBTVRKRVZ4ZFdsbVlYZ2dVMlZqZFhKbA0KSUVkc2IySmhiQ0JsUW5WemFXNWxjM01nUTBFdE1UQ0JuekFOQmdrcWhraUc5dzBCQVFFRkFBT0JqUUF3DQpnWWtDZ1lFQXV1Y1hrQUpsc1RSVlBFbkNVZFhmcDlFM2o5SG5nWE5CVW1DYm5hRVhKbml0eDdIb0pwUXkNCnRkNHpqVG92Mi9LYWVscHptS05jNmZ1S2N4dGM1OE8vZ0d6TnFmVFdLOEQzK1ptcVk2S3hSd0lQMU9SUg0KT2hJOGJJcGFWSVJ3MjhIRmtNOXlSY3VvV2NETk01MC9vNWJyaFRNaEhENGVQbUJ1ZHB4bmhjWEl3MkVDDQpBd0VBQWFObU1HUXdFUVlKWUlaSUFZYjRRZ0VCQkFRREFnQUhNQThHQTFVZEV3RUIvd1FGTUFNQkFmOHcNCkh3WURWUjBqQkJnd0ZvQVV2cWlnZEhKUWEwUzN5U1BZKzZqL3MxZHJhR3d3SFFZRFZSME9CQllFRkw2bw0Kb0hSeVVHdEV0OGtqMlB1by83TlhhMmhzTUEwR0NTcUdTSWIzRFFFQkJBVUFBNEdCQUREaUFWR3F4K3BmDQoycm5RWlE4dzFqN2FEUlJKYnBHVEp4UXg3OFQzTFVYNDdNZS9va0VOSTdTUytSa0FaNzBCcjgzZ2NmeGENCnoyVEU0SmFZMEtOQTRnR0s3eWNIOFdVQmlrUXRCbVYxVXNDR0VDQWhYMnhyRDJ5dUNSeXY4cUlZTk1SMQ0KcEhNYzhZM2M3NjM1czNhMGtyL2NsUkFldnN2SU8xcUVZQmxXbEtsVg0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLSANCkVRVUlGQVgNCn0NCg0KIyMjDQojIyMgb3ZlcldyaXRlQ29uZigpDQojIyMJb3ZlcndyaXRlIHRoZSBkZWZhdWx0IHN0b3JrLmNvbmYgZmlsZQ0KIyMjICAgICB0aGF0IHdhcyBpbnN0YWxsZWQgYnkgdGhlIHJwbSBwYWNrYWdlLg0KIyMjICAgICB0aGlzIGlzIGEgdGVtcG9yYXJ5IGhhY2sgYmVjYXVzZSBJIG5lZWQNCiMjIyAgICAgdG8gY2hhbmdlIHRoZSBuZXN0cG9ydCBhbmQgSSBkb250IGtub3cNCiMjIyAgICAgZW5vdWdoIHRvIHJlcGFja2FnZSB0aGUgcnBtIHdpdGggdGhlDQojIyMgICAgIGNvcnJlY3Qgc2V0dGluZ3MNCmZ1bmN0aW9uIG92ZXJXcml0ZUNvbmYoKXsNCmNhdCA+IC91c3IvbG9jYWwvc3RvcmsvZXRjL3N0b3JrLmNvbmYgPDxFTkRPRkZJTEUNCnBhY21hbj0vdXNyL2xvY2FsL3N0b3JrL2Jpbi9wYWNtYW4NCmR0ZC1wYWNrYWdlcz0vdXNyL2xvY2FsL3N0b3JrL2Jpbi9wYWNrYWdlcy5kdGQNCmR0ZC1ncm91cHM9L3Vzci9sb2NhbC9zdG9yay9iaW4vZ3JvdXBzLmR0ZA0Kc3RvcmtuZXN0dXBkYXRlbGlzdGVuZXJwb3J0PTY0OQ0KDQojYml0dG9ycmVudHRyYWNrZXJob3N0PXF1YWRydXMuY3MuYXJpem9uYS5lZHUNCmJpdHRvcnJlbnR0cmFja2VyaG9zdD1ucjA2LmNzLmFyaXpvbmEuZWR1DQoNCmJpdHRvcnJlbnR0cmFja2VycG9ydD02ODgwDQpiaXR0b3JyZW50dXBsb2FkcmF0ZT0wDQpiaXR0b3JyZW50c2VlZGxvb2t1cHRpbWVvdXQ9MzANCg0KI3BhY2thZ2VyZXBvc2l0b3J5ID0gcXVhZHJ1cy5jcy5hcml6b25hLmVkdS9QbGFuZXRMYWIvVjN8ZGlzdCwgc3RhYmxlDQpwYWNrYWdlcmVwb3NpdG9yeSA9IG5yMDYuY3MuYXJpem9uYS5lZHUvUGxhbmV0TGFiL1YzfGRpc3QsIHN0YWJsZQ0KI3BhY2thZ2VpbmZvcmVwb3NpdG9yeSA9IHF1YWRydXMuY3MuYXJpem9uYS5lZHUvUGxhbmV0TGFiL1YzL3N0b3JrLmluZm8NCnBhY2thZ2VpbmZvcmVwb3NpdG9yeSA9IG5yMDYuY3MuYXJpem9uYS5lZHUvUGxhbmV0TGFiL1YzL3N0b3JrLmluZm8NCg0KdXNlcm5hbWUgPSBQbGFuZXRMYWINCnB1YmxpY2tleWZpbGUgPSAvdXNyL2xvY2FsL3N0b3JrL3Zhci9rZXlzL1BsYW5ldExhYi5wdWJsaWNrZXkNCnBhY2thZ2VtYW5hZ2VycyA9IG5lc3RycG0sIHJwbSwgdGFyZ3oNCnRyYW5zZmVybWV0aG9kPSBuZXN0LGJpdHRvcnJlbnQsY29ibGl0eixjb3JhbCxodHRwLGZ0cA0KbmVzdHBvcnQ9NjAwMA0KdGFycGFja2luZm9wYXRoPS91c3IvbG9jYWwvc3RvcmsvdmFyL3RhcmluZm8NCkVORE9GRklMRQ0KfSANCg0KDQojIyMNCiMjIyBkb3dubG9hZE5SMDYoKQ0KIyMjICAgIGRvd25sb2FkIGEgZmlsZSBmcm9tIG5yMDYgdXNpbmcgY3VybA0KIyMjDQojIyMgYXJnczogDQojIyMgICAgICAgLSB0aGUgcGF0aCBvZiB0aGUgZmlsZSB5b3Ugd2lzaCB0byBkb3dubG9hZA0KIyMjICAgICAgICAgcmVsYXRpdmUgZnJvbSBodHRwczovL25yMDYuY3MuYXJpem9uYS5lZHUNCiMjIyAgICAgICAtIHRoZSBmaWxlIHRvIHNhdmUgaXQgdG8NCiMjIyAgICAgICAtIHJldHVybmVkIHZhbHVlIGFzIHNwZWNpZmllZCBpbiB2ZXJpZnlEb3dubG9hZA0KZnVuY3Rpb24gZG93bmxvYWROUjA2KCl7DQogICAgY3VybCAtLWNhY2VydCAkQ0VSVCBodHRwczovL25yMDYuY3MuYXJpem9uYS5lZHUvJDEgLW8gJDIgMj4vZGV2L251bGwNCiAgICB2ZXJpZnlEb3dubG9hZCAkMiAkMw0KfQ0KDQojIyMNCiMjIyB2ZXJpZnlEb3dubG9hZCgpDQojIyMgICAgIHZlcmlmeSB0aGF0IGEgZmlsZSB0aGF0IHdhcyBqdXN0IGRvd25sb2FkIHdpdGggZG93bmxvYWROUjA2DQojIyMgICAgIHdhcyBkb3dubG9hZCBjb3JyZWN0bHkuIFNpbmNlIHdlIGFyZSBnZXR0aW5nIHN0dWZmIGZyb20gYQ0KIyMjICAgICBodHRwIHNlcnZlciB3ZSBhcmUgYXNzdW1pbmcgdGhhdCBpZiB3ZSBnZXQgYSA0MDQgcmVzcG9uc2UNCiMjIyAgICAgdGhhdCB0aGUgcGFnZSB3ZSB3YW50IGRvZXMgbm90IGV4aXN0LiBBbHNvLCBpZiB0aGUgb3V0cHV0IGZpbGUNCiMjIyAgICAgZG9lcyBub3QgZXhpc3QgdGhhdCBtZWFucyB0aGF0IG9ubHkgaGVhZGVycyB3ZXJlIHJldHVybmVkDQojIyMgICAgIHdpdGhvdXQgYW55IGNvbnRlbnQuIHRoaXMgdG9vIGlzIGEgaW52YWxpZCBmaWxlIGRvd25sb2FkDQojIyMNCiMjIyBhcmdzOg0KIyMjICAgICAgIC0gdGhlIGZpbGUgdG8gdmVyaWZ5DQojIyMgICAgICAgLSByZXR1cm4gdmFyaWFibGUsIHdpbGwgaGF2ZSAxIGlmIGZhaWwgMCBpZiBnb29kDQojIyMNCmZ1bmN0aW9uIHZlcmlmeURvd25sb2FkKCl7DQogICAgZXZhbCAiJDI9MCINCiAgICBpZiBbICEgLWYgJDEgXTsNCiAgICB0aGVuDQogICAgICAgIGV2YWwgIiQyPTEiDQogICAgZWxpZiBncmVwICc0MDQgTm90IEZvdW5kJyAkMSA+IC9kZXYvbnVsbA0KICAgIHRoZW4NCglybSAtZiAkMQ0KICAgICAgICBldmFsICIkMj0xIg0KICAgIGVsc2UNCiAgICAgICAgZXZhbCAiJDI9MCINCiAgICBmaQ0KfQ0KDQoNCiMgY2hlY2sgZm9yIHJvb3QgdXNlcg0KaWYgWyAkVUlEIC1uZSAiMCIgXQ0KdGhlbg0KICAgZWNobyAiWW91IG11c3QgcnVuIHRoaXMgcHJvZ3JhbSB3aXRoIHJvb3QgcGVybWlzc2lvbnMuLi4iDQogICBlcnJvcg0KZmkgICANCiANCiMgY2xlYW4gdXAgaW4gY2FzZSB0aGlzIHNjcmlwdCB3YXMgcnVuIGJlZm9yZSBhbmQgZmFpbGVkDQpybSAtcmYgL3RtcC9zdG9yayAmPiAvZGV2L251bGwNCg0KIyBjcmVhdGUgL3RtcC9zdG9yayBkaXJlY3RvcnkNCm1rZGlyIC90bXAvc3RvcmsgDQppZiBbICQ/IC1uZSAiMCIgXQ0KdGhlbg0KICAgZWNobw0KICAgZWNobyAiQ291bGQgbm90IGNyZWF0ZSB0aGUgL3RtcC9zdG9yayBkaXJlY3RvcnkuLi4iDQogICBlcnJvcg0KZmkNCg0KIyBleHBvcnQgb3VyIHJvb3QgZGlyZWN0b3J5IHRvIFN0b3JrDQplY2hvICJhcml6b25hX3N0b3JrMiIgPiAvLmV4cG9ydGRpcg0KaWYgWyAkPyAtbmUgIjAiIF0NCnRoZW4NCiAgIGVjaG8NCiAgIGVjaG8gIkNvdWxkIG5vdCBjcmVhdGUgdGhlIC8uZXhwb3J0ZGlyIGZpbGUuLi4iDQogICBlcnJvcg0KZmkNCiANCiMgdGVsbCBzdG9yayB0aGF0IHdlIHdhbnQgdG8gYmUgc2VydmVkDQppZiBbIC1mIC9ldGMvc2xpY2VuYW1lIF0NCnRoZW4NCiAgIFNMSUNFTkFNRT1gY2F0IC9ldGMvc2xpY2VuYW1lYA0KZWxzZSANCiAgIFNMSUNFTkFNRT0kVVNFUg0KZmkNCndnZXQgLU8gL3RtcC9zdG9yay8kU0xJQ0VOQU1FICJodHRwOi8vbG9jYWxob3N0OjY0OC8kU0xJQ0VOQU1FXCRiaW5kc2NyaXB0Ig0KDQojIHZlcmlmeSB0aGF0IHRoZSBkb3dubG9hZCB3YXMgc3VjY2Vzc2Z1bA0KaWYgWyAhIC1mIC90bXAvc3RvcmsvJFNMSUNFTkFNRSAtbyAkPyAtbmUgMCBdDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJTdG9yayBkb2Vzbid0IHNlZW0gdG8gYmUgcnVubmluZyBvbiB0aGlzIG5vZGUuLi4iDQogICBlcnJvcg0KZmkNCg0KIyB3YWl0IGZvciBzdG9yayBzbGljZSANCmVjaG8gIldhaXRpbmcgZm9yIFN0b3JrIHRvIGFjY2VwdCBvdXIgYmluZGluZy4uLiINCndoaWxlIFsgISAtZiAvdG1wL3N0b3JrL3N0b3JrX3NheXNfZ28gXQ0KZG8NCiAgIHNsZWVwIDENCmRvbmUNCg0KIyBjaGFuZ2UgUFdEIHRvIHRoZSAvdG1wL3N0b3JrIGRpcmVjdG9yeSANCmNkIC90bXAvc3RvcmsNCmlmIFsgJD8gLW5lICIwIiBdDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJDb3VsZCBub3QgYWNjZXNzIHRoZSAvdG1wL3N0b3JrIGRpcmVjdG9yeS4uLiINCiAgIGVycm9yDQpmaQ0KDQojIGNvbmZpcm0gdGhhdCBwYWNrYWdlcyB0byBiZSBpbnN0YWxsZWQgYWN0dWFsbHkgZXhpc3QNCmlmIGVjaG8gKi5ycG0gfCBncmVwICcqJyA+IC9kZXYvbnVsbA0KdGhlbg0KICAgZWNobw0KICAgZWNobyAiRXJyb3I6IFN0b3JrIHBhY2thZ2UgZG93bmxvYWQgZmFpbGVkLi4uIg0KICAgZXJyb3INCmZpDQoNCiMgcmVtb3ZlIFN0b3JrIHBhY2thZ2VzIGFuZCBmaWxlcw0KZWNobw0KZWNobyAiUmVtb3ZpbmcgU3RvcmsgZmlsZXMuLi4iDQoNCiMgYnVpbGQgYSBsaXN0IG9mIHBhY2thZ2VzIHRvIHJlbW92ZQ0KcGFja2FnZXM9IiINCmZvciBmaWxlbmFtZSBpbiAqLnJwbQ0KZG8NCiAgIyBjb252ZXJ0IGZpbGVuYW1lIHRvIGEgcGFja2FnZSBuYW1lDQogIHBhY2s9YHJwbSAtcXAgLS1xZiAiJXtOQU1FfVxuIiAkZmlsZW5hbWVgDQogIGlmIFsgJD8gLWVxICIwIiBdDQogIHRoZW4NCiAgICBwYWNrYWdlcz0iJHBhY2thZ2VzICRwYWNrIg0KICBmaQ0KZG9uZSAgIA0KDQojIHJlbW92ZSBvbGQgU3RvcmsgcGFja2FnZXMNCnJwbSAtZSAkcGFja2FnZXMgJj4gL2Rldi9udWxsDQoNCiMgcmVtb3ZlIGFueXRoaW5nIGxlZnQgaW4gL3Vzci9sb2NhbC9zdG9yay9iaW4NCnJtIC1yZiAvdXNyL2xvY2FsL3N0b3JrL2Jpbi8qICY+IC9kZXYvbnVsbCANCg0KIyBpbnN0YWxsIFN0b3JrIHBhY2thZ2VzDQplY2hvDQplY2hvICJJbnN0YWxsaW5nIHBhY2thZ2VzLi4uIiANCg0KIyBidWlsZCBhIGxpc3Qgb2YgcGFja2FnZXMgdG8gaW5zdGFsbA0KcGFja2FnZXM9IiINCmZvciBmaWxlbmFtZSBpbiAqLnJwbQ0KZG8NCiAgcGFja2FnZXM9IiRwYWNrYWdlcyAkZmlsZW5hbWUiDQpkb25lICAgDQoNCiMgaW5zdGFsbCB0aGUgbmV3IHN0b3JrIHBhY2thZ2VzDQpycG0gLWkgJHBhY2thZ2VzDQoNCiMgcmVwb3J0IHBhY2thZ2UgaW5zdGFsbGF0aW9uIGVycm9ycw0KaWYgWyAkPyAtbmUgIjAiIF0NCnRoZW4NCiAgZWNobyAiV2FybmluZzogUG9zc2libGUgZXJyb3IgaW5zdGFsbGluZyBTdG9yayBwYWNrYWdlcy4uLiINCmZpDQoNCiMgcmVzdG9yZSBvcmlnaW5hbCBQV0QNCmNkICRPTERQV0QNCg0KIyBjbGVhbiB1cCB0ZW1wb3JhcnkgZmlsZXMNCnJtIC1yZiAvdG1wL3N0b3JrICY+IC9kZXYvbnVsbA0KDQojIFNFRSBUTy1ETyAxDQojY3JlYXRlIHRoZSBlcXVpZmF4IGNlcnRpZmljYXRlIHRvIHVzZSBmb3IgY3VybA0KI2NyZWF0ZUNlcnRpZmljYXRlDQoNCiMgVE8tRE8gMQ0KIyBpbXBsZW1lbnQgdGhlIGJlbG93IGluIHRoZSBiZWdnaW5pbmcgb2Ygc3RvcmsucHkNCiNhdHRlbXB0IHRvIGRvd25sb2FkIHRoZSB1c2VycyBwdWJsaWMga2V5IGZyb20gdGhlIHJlcG9zaXRvcnkNCiNkb3dubG9hZE5SMDYgInVzZXItdXBsb2FkL3B1YmtleXMvJFNMSUNFTkFNRS5wdWJsaWNrZXkiICIvdXNyL2xvY2FsL3N0b3JrL3Zhci8kU0xJQ0VOQU1FLnB1YmxpY2tleSIgUkVUDQoNCiNpZiBbICRSRVQgLW5lIDAgXTsNCiN0aGVuDQojICAgZWNobw0KIyAgIGVjaG8gIkNvdWxkIG5vdCBmZXRjaCB5b3VyIHB1YmxpYyBrZXkgZnJvbSB0aGUgcmVwb3NpdG9yeS4iDQojICAgZWNobyAiSWYgeW91IHdhbnQgdG8gdXBsb2FkIG9uZSBmb3IgdGhlIG5leHQgdGltZSB5b3UgcnVuIg0KIyAgIGVjaG8gInRoZSBpbml0c2NyaXB0IHBsZWFzZSB2aXNpdCINCiMgICBlY2hvICJodHRwOi8vbnIwNi5jcy5hcml6b25hLmVkdS90ZXN0cGhwL3VwbG9hZC5waHAiDQojICAgZWNobw0KI2ZpDQoNCiNhdHRlbXB0IHRvIGRvd25sb2FkIHRoZSB1c2VycyBzdG9yay5jb25mIGZpbGUgZnJvbSB0aGUgcmVwb3NpdG9yeQ0KI2Rvd25sb2FkTlIwNiAidXNlci11cGxvYWQvY29uZi8kU0xJQ0VOQU1FLnN0b3JrLmNvbmYiICIvdXNyL2xvY2FsL3N0b3JrL2V0Yy9zdG9yay5jb25mLnVzZXJzIiBSRVQNCg0KI2lmIFsgJFJFVCAtbmUgMCBdOw0KI3RoZW4NCiMgICBlY2hvDQojICAgZWNobyAiQ291bGQgbm90IGZldGNoIHlvdXIgc3RvcmsuY29uZiBmaWxlIGZyb20gdGhlIHJlcG9zaXRvcnkuIg0KIyAgIGVjaG8gIklmIHlvdSB3YW50IHRvIHVwbG9hZCBvbmUgZm9yIHRoZSBuZXh0IHRpbWUgeW91IHJ1biINCiMgICBlY2hvICJ0aGUgaW5pdHNjcmlwdCBwbGVhc2UgdmlzaXQiDQojICAgZWNobyAiaHR0cDovL25yMDYuY3MuYXJpem9uYS5lZHUvdGVzdHBocC91cGxvYWQucGhwIg0KIyAgIGVjaG8gIlN0b3JrIHdpbGwgd29yayB3aXRob3V0IGEgY29uZmlndXJhdGlvbiBmaWxlIGJ1dCB0byBtYWtlIG9uZSINCiMgICBlY2hvICJwbGVhc2UgcGxhY2UgYSBmaWxlIG5hbWVkIHN0b3JrLmNvbmYgaW4gL3Vzci9sb2NhbC9zdG9yay9ldGMiDQojICAgZWNobyAicmVmZXIgdG8gdGhlIG1hbnVhbCBmb3IgbW9yZSBkaXJlY3Rpb25zIG9yIGVtYWlsOiINCiMgICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhZGRpdGlvbmFsIGFzc2lzdGFuY2UuIg0KIyAgIGVjaG8NCiNmaQ0KDQojZG9udCBuZWVkIHRvIG92ZXJ3cml0ZSB0aGUgZGVmYXVsdCBjb25mIGZpbGUNCiNiZWNhdXNlIGl0IHNob3VsZCBiZSBmaXhlZCBpbiB0aGUgbmV3IHJwbXMNCiNvdmVyV3JpdGVDb25mDQoNCiMgcnVuIHN0b3JrIHRvIHVwZGF0ZSBrZXlmaWxlcyBhbmQgZG93bmxvYWQgcGFja2FnZSBsaXN0cw0KZWNobw0KZWNobyAiQXR0ZW1wdGluZyB0byBjb21tdW5pY2F0ZSB3aXRoIHN0b3JrLi4uIg0KaWYgc3RvcmsgDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJDb25ncmF0dWxhdGlvbnMsIHlvdSBoYXZlIHN1Y2Nlc3NmdWxseSBib3VuZCB0byBzdG9yayEiDQogICBlY2hvDQogICBlY2hvICJGb3IgaGVscCwgeW91IG1heSB0eXBlIHN0b3JrIC0taGVscCINCiAgIGVjaG8NCiAgICNlY2hvICJUaGVyZSBpcyBhbHNvIGEgc3RvcmtxdWVyeSBjb21tYW5kIHRoYXQgd2lsbCBwcm92aWRlIGluZm9ybWF0aW9uIg0KICAgI2VjaG8gImFib3V0IHBhY2thZ2VzIGluIHRoZSByZXBvc2l0b3J5LiINCiAgIGVjaG8NCiAgIGVjaG8gIkZvciBtb3JlIGhlbHAsIHZpc2l0IHRoZSBzdG9yayBwcm9qZWN0IG9ubGluZSBhdCINCiAgIGVjaG8gImh0dHA6Ly93d3cuY3MuYXJpem9uYS5lZHUvc3RvcmsvLiAgUGxlYXNlIGNvbnRhY3QiDQogICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhZGRpdGlvbmFsIGFzc2lzdGFuY2UuIiANCiAgICNybSAtZiAkQ0VSVCA+IC9kZXYvbnVsbA0KZWxzZQ0KICAgZWNobw0KICAgZWNobyAiQW4gZXJyb3Igb2NjdXJyZWQgZHVyaW5nIGluc3RhbGwgZmluYWxpemF0aW9uLi4uICBQbGVhc2UgY29udGFjdCINCiAgIGVjaG8gInN0b3JrLXN1cHBvcnRAY3MuYXJpem9uYS5lZHUgZm9yIGFzc2lzdGFuY2UuIg0KICAgI3JtIC1mICRDRVJUID4gL2Rldi9udWxsDQogICBleGl0IDENCmZpDQoNCiMgZG9uZQ0KZXhpdCAwDQo=', 'name': 'arizona_stork_2', 'encoding': 'base64'}, {'initscript_id': 9, 'script': 'IyEvYmluL2Jhc2gNCmNkIC8NCnJtIC1mIHN0YXJ0X3B1cnBsZQ0Kd2dldCBodHRwOi8vd3d3LmNzLnByaW5jZXRvbi5lZHUvfmRlaXNlbnN0L3B1cnBsZS9zdGFydF9wdXJwbGUNCmNobW9kIDc1NSBzdGFydF9wdXJwbGUNCnN1IHByaW5jZXRvbl9wdXJwbGUgLWMgJy4vc3RhcnRfcHVycGxlJw0K', 'name': 'princeton_purple', 'encoding': 'base64'}, {'initscript_id': 6, 'script': 'IyEgL2Jpbi9zaA0KDQojIHNhdmUgb3JpZ2luYWwgUFdEDQpPTERQV0Q9JFBXRA0KDQojIGVycm9yIHJlcG9ydGluZyBmdW5jdGlvbg0KZXJyb3IoKQ0Kew0KICAgZWNobw0KICAgZWNobyAiUGxlYXNlIEUtbWFpbCBzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGlmIHlvdSBiZWxpZXZlIHlvdSBoYXZlIiANCiAgIGVjaG8gInJlY2VpdmVkIHRoaXMgbWVzc2FnZSBpbiBlcnJvci4iDQoNCiAgICMgcmVzdG9yZSBvcmlnaW5hbCBQV0QNCiAgIGNkICRPTERQV0QNCiAgIGV4aXQgMQ0KfQ0KDQojIGNoZWNrIGZvciByb290IHVzZXINCmlmIFsgJFVJRCAtbmUgIjAiIF0NCnRoZW4NCiAgIGVjaG8gJ1lvdSBtdXN0IGJlIHJvb3QgdG8gcnVuIHRoaXMgcHJvZ3JhbS4uLicNCiAgIGVycm9yDQpmaSAgIA0KIA0KIyBDbGVhbiB1cCBpbiBjYXNlIEkgcmFuIHRoaXMgYmVmb3JlDQpybSAtZiAvdG1wL3N0b3JrKiA+IC9kZXYvbnVsbCAyPiYxDQoNCiMgRmlyc3Qgb2YgYWxsIGV4cG9ydCBvdXIgcm9vdCBkaXJlY3RvcnkgdG8gU3RvcmsNCmVjaG8gImFyaXpvbmFfc3RvcmsiID4gLy5leHBvcnRkaXINCiANCiMgTm93IHRlbGwgc3RvcmsgdGhhdCB3ZSB3YW50IHRvIGJlIHNlcnZlZA0KaWYgWyAtZiAvZXRjL3NsaWNlbmFtZSBdDQp0aGVuDQogICBTTElDRU5BTUU9YGNhdCAvZXRjL3NsaWNlbmFtZWANCmVsc2UgDQogICBTTElDRU5BTUU9JFVTRVINCmZpDQoNCndnZXQgaHR0cDovL2xvY2FsaG9zdDo2NDAvJFNMSUNFTkFNRQ0KDQojIGNoZWNrIHRvIG1ha2Ugc3VyZSB0aGUgZG93bmxvYWQgd2FzIHN1Y2Nlc3NmdWwNCmlmIFsgISAtZiAkU0xJQ0VOQU1FIC1vICQ/IC1uZSAwIF0NCnRoZW4NCiAgIGVjaG8NCiAgIGVjaG8gIlN0b3JrIGRvZXNuJ3Qgc2VlbSB0byBiZSBydW5uaW5nIG9uIHRoaXMgbm9kZS4uLiINCiAgIGVycm9yDQpmaQ0KDQojIHdhaXQgZm9yIHN0b3JrIHNsaWNlIA0KZWNobyAiV2FpdGluZyBmb3IgU3RvcmsgdG8gYWNjZXB0IG91ciBiaW5kaW5nLi4uIg0Kd2hpbGUgWyAhIC1mIC90bXAvc3Rvcmtfc2F5c19nbyBdDQpkbw0KICAgc2xlZXAgMQ0KZG9uZQ0KDQojIGNoYW5nZSBQV0QgdG8gdGhlIC90bXAgZGlyZWN0b3J5IA0KY2QgL3RtcA0KaWYgWyAkPyAtbmUgIjAiIF0NCnRoZW4NCiAgIGVjaG8NCiAgIGVjaG8gIkNvdWxkIG5vdCBhY2Nlc3MgdGhlIC90bXAgZGlyZWN0b3J5Li4uIg0KICAgZXJyb3INCmZpDQoNCiMgY29uZmlybSB0aGF0IHBhY2thZ2VzIHRvIGJlIGluc3RhbGxlZCBhY3R1YWxseSBleGlzdA0KaWYgZWNobyAqLnJwbSB8IGdyZXAgJyonID4gL2Rldi9udWxsDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJFcnJvcjogU3RvcmsgcGFja2FnZSBkb3dubG9hZCBmYWlsZWQuLi4iDQogICBlcnJvcg0KZmkNCg0KIyBpbnN0YWxsIFN0b3JrIHBhY2thZ2VzDQplY2hvICJJbnN0YWxsaW5nIHBhY2thZ2VzLi4uIiANCmZvciBwYWNrIGluICoucnBtDQpkbw0KICAgIyByZW1vdmUgdGhlIG9sZCBzdG9yayBwYWNrYWdlLCBpZiBhbnkNCiAgIHJwbSAtZSBgcnBtIC1xcCAtLXFmICIle05BTUV9XG4iICRwYWNrYCA+IC9kZXYvbnVsbCAyPiYxDQoNCiAgICMgcmVtb3ZlIGFueXRoaW5nIGxlZnQgaW4gL3Vzci9sb2NhbC9zdG9yay9iaW4NCiAgIHJtIC1yZiAvdXNyL2xvY2FsL3N0b3JrL2Jpbi8qID4gL2Rldi9udWxsIDI+JjENCg0KICAgIyBpbnN0YWxsIHRoZSBuZXcgc3RvcmsgcGFja2FnZQ0KICAgcnBtIC1pICRwYWNrDQoNCiAgICMgcmVwb3J0IHBhY2thZ2UgaW5zdGFsbGF0aW9uIGVycm9ycw0KICAgaWYgWyAkPyAtbmUgIjAiIF0NCiAgIHRoZW4NCiAgICAgZWNobyAiV2FybmluZzogUG9zc2libGUgZXJyb3IgaW5zdGFsbGluZyBTdG9yayBwYWNrYWdlOiAkcGFjay4uLiINCiAgIGZpDQpkb25lDQoNCiMgcmVzdG9yZSBvcmlnaW5hbCBQV0QNCmNkICRPTERQV0QNCg0KIyBjbGVhbiB1cCB0ZW1wb3JhcnkgZmlsZXMNCnJtIC1mIC90bXAvc3RvcmsqID4gL2Rldi9udWxsIDI+JjENCnJtICRTTElDRU5BTUUqIA0KDQojIHJ1biBzdG9yayB0byB1cGRhdGUga2V5ZmlsZXMgYW5kIGRvd25sb2FkIHBhY2thZ2UgbGlzdHMNCmVjaG8gIkF0dGVtcHRpbmcgdG8gY29tbXVuaWNhdGUgd2l0aCBzdG9yay4uLiINCmlmIHN0b3JrIA0KdGhlbg0KICAgZWNobw0KICAgZWNobyAiQ29uZ3JhdHVsYXRpb25zLCB5b3UgaGF2ZSBzdWNjZXNzZnVsbHkgYm91bmQgdG8gc3RvcmshIg0KICAgZWNobw0KICAgZWNobyAiRm9yIGhlbHAsIHlvdSBtYXkgdHlwZSBzdG9yayAtLWhlbHAgIg0KICAgZWNobw0KICAgZWNobyAiVGhlcmUgaXMgYWxzbyBhIHN0b3JrcXVlcnkgY29tbWFuZCB0aGF0IHdpbGwgcHJvdmlkZSBpbmZvcm1hdGlvbiINCiAgIGVjaG8gImFib3V0IHBhY2thZ2VzIGluIHRoZSByZXBvc2l0b3J5LiINCiAgIGVjaG8NCiAgIGVjaG8gIkZvciBtb3JlIGhlbHAsIHZpc2l0IHRoZSBzdG9yayBwcm9qZWN0IG9ubGluZSBhdCINCiAgIGVjaG8gImh0dHA6Ly93d3cuY3MuYXJpem9uYS5lZHUvc3RvcmsvLiAgUGxlYXNlIGNvbnRhY3QiDQogICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhZGRpdGlvbmFsIGFzc2lzdGFuY2UuIiANCmVsc2UNCiAgIGVjaG8NCiAgIGVjaG8gIkFuIGVycm9yIG9jY3VycmVkIGR1cmluZyBpbnN0YWxsIGZpbmFsaXphdGlvbi4uLiAgUGxlYXNlIGNvbnRhY3QiDQogICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhc3Npc3RhbmNlLiINCiAgIGV4aXQgMQ0KZmkNCg0KIw0KIyBIZWxsbyBXb3JsZCBkZW1vIGNvZGUNCiMNCg0KIyBQdWJsaWMga2V5IGZvciB0aGlzIGRlbW8NCmNhdCA+L3Vzci9sb2NhbC9zdG9yay92YXIva2V5cy9oZWxsby5wdWJsaWNrZXkgPDwiRU9GIg0KLS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0NCk1Gd3dEUVlKS29aSWh2Y05BUUVCQlFBRFN3QXdTQUpCQU1XcVE3K2VxQVljNlRPSUJPbkJyRnZqYjlnRVViaWgNCkkxd0Nyeld4a09aa01BcXFmY1RuMW9tcCtLMGd0cUtBK3VaNEIzRGlQRXI0Q0V0Myt5MmJlMGtDQXdFQUFRPT0NCi0tLS0tRU5EIFBVQkxJQyBLRVktLS0tLQ0KRU9GDQpzZWQgLWkgLWUgJ3MvXnVzZXJuYW1lLiovdXNlcm5hbWUgPSBoZWxsby8nIC91c3IvbG9jYWwvc3RvcmsvZXRjL3N0b3JrLmNvbmYNCg0KIyBJbnN0YWxsIFJQTQ0Kc3RvcmsgdXBncmFkZSBoZWxsbw0KDQojIGVuZA0KZXhpdCAwDQo=', 'name': 'princeton_hello_stork', 'encoding': 'base64'}, {'initscript_id': 10, 'script': 'IyEvYmluL2Jhc2gNCg0KIyBJbml0IHNjcmlwdCBmb3IgdGhlIFBsYW5ldExhYiAiSGVsbG8gV29ybGQiIGRlbW8gdXNpbmcgR29vZ2xlIEVhcnRoLg0KIyBJbnN0YWxscyBhIGNyb250YWIgZW50cnkgb24gdGhlIG5vZGUgdGhhdCBwaG9uZXMgaG9tZSB0byB0aGUgc2VydmVyDQojIGV2ZXJ5IHRocmVlIG1pbnV0ZXMuDQoNClNFUlZFUj0xMjguMTEyLjEzOS43Mzo4MDQyCQkjIHBsYW5ldGxhYi0zLmNzLnByaW5jZXRvbi5lZHUNCg0KL3Vzci9iaW4vY3VybCAtcyBodHRwOi8vJFNFUlZFUi8NCmVjaG8gIiovNSAqICogKiAqIC91c3IvYmluL2N1cmwgLXMgaHR0cDovLyRTRVJWRVIvIiB8IGNyb250YWIgLQ0KL3NiaW4vY2hrY29uZmlnIGNyb25kIG9uDQo=', 'name': 'princeton_hello', 'encoding': 'base64'}]])

# Convert plc_initscript.initscript_id to raw initscript attribute
for slice_attribute in GetSliceAttributes({'name': 'plc_initscript'}):
    id = slice_attribute['slice_attribute_id']
    slice_id = slice_attribute['slice_id']
    initscript_id = int(slice_attribute['value'])

    # Delete old attribute
    DeleteSliceAttribute(id)

    if initscript_id not in initscripts:
        print "Warning: Missing initscript %d" % initscript_id
        continue

    initscript = base64.b64decode(initscripts[initscript_id]['script'])

    # Add as initscript attribute
    AddSliceAttribute(slice_id, 'initscript', initscript)

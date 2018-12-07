#!/usr/bin/env /usr/bin/plcsh
#
# Convert old planetlab3 slice attributes and initscripts to new
# planetlab4 ones.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

import re
import base64

# Convert nm_net_{exempt_,}{min,max}_rate (bps) to
# net_{i2_,}{min,max}_rate and net_{i2_,}{min,max}_rate (kbps)
rename = {'nm_net_min_rate': 'net_min_rate',
          'nm_net_max_rate': 'net_max_rate',
          'nm_net_exempt_min_rate': 'net_i2_min_rate',
          'nm_net_exempt_max_rate': 'net_i2_max_rate'}
for slice_attribute in GetSliceTags({'name': list(rename.keys())}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Convert bps to kbps
    bps = int(slice_attribute['value'])
    kbps = bps / 1000

    # Add the new attribute
    if GetSlices([slice_id]):
        AddSliceTag(slice_id, rename[name], str(kbps))

    # Delete the old attribute
    DeleteSliceTag(id)

# Convert nm_net_{exempt_,}avg_rate to
# net_{i2_,}max_kbyte and net_{i2_,}thresh_kbyte
rename = {'nm_net_avg_rate': {'max': 'net_max_kbyte',
                              'thresh': 'net_thresh_kbyte'},
          'nm_net_exempt_avg_rate': {'max': 'net_i2_max_kbyte',
                                     'thresh': 'net_i2_thresh_kbyte'}}
for slice_attribute in GetSliceTags({'name': list(rename.keys())}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Convert bps to 80% and 100% of max bytes per day
    bps = int(slice_attribute['value'])
    max_kbyte = bps * 24 * 60 * 60 / 8 / 1000
    thresh_kbyte = int(0.8 * max_kbyte)

    # Add the new attribute
    if GetSlices([slice_id]):
        AddSliceTag(slice_id, rename[name]['max'], str(max_kbyte))
        AddSliceTag(slice_id, rename[name]['thresh'], str(thresh_kbyte))

    # Delete the old attribute
    DeleteSliceTag(id)

# Convert plc_slice_state
for slice_attribute in GetSliceTags({'name': 'plc_slice_state'}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Add the new attribute
    if GetSlices([slice_id]):
        if slice_attribute['value'] == "suspended":
            AddSliceTag(slice_id, 'enabled', "0")
        else:
            AddSliceTag(slice_id, 'enabled', "1")

    # Delete the old attribute
    DeleteSliceTag(id)
    
# Straight renames
rename = {'nm_cpu_share': 'cpu_share',
          'nm_disk_quota': 'disk_max',
          'nm_net_share': 'net_share',
          'nm_net_exempt_share': 'net_i2_share',
          'nm_net_max_byte': 'net_max_kbyte',
          'nm_net_max_thresh_byte': 'net_thresh_kbyte',
          'nm_net_max_exempt_byte': 'net_i2_max_kbyte',
          'nm_net_max_thresh_exempt_byte': 'net_i2_thresh_kbyte'}
for slice_attribute in GetSliceTags({'name': list(rename.keys())}):
    id = slice_attribute['slice_attribute_id']
    name = slice_attribute['name']
    slice_id = slice_attribute['slice_id']

    # Pass straight through
    value = slice_attribute['value']

    # Add the new attribute
    if GetSlices([slice_id]):
        AddSliceTag(slice_id, rename[name], value)

    # Delete the old attribute
    DeleteSliceTag(id)

# Update plc_ticket_pubkey attribute
for slice_attribute in GetSliceTags({'name': "plc_ticket_pubkey"}):
    id = slice_attribute['slice_attribute_id']

    UpdateSliceTag(id, """
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDKXa72MEKDAnVyzEpKOB1ot2eW
xG/TG2aa7q/2oy1xf5XMmU9H9uKwO+GoUeinp1BSxgkVRF0VhEGGaqKR9kYQzX0k
ht4+P2hAr+UyU4cp0NxV4xfmyAbrNKuHVjawMUCu5BH0IkBUC/89ckxk71oROnak
FbI7ojUezSGr4aVabQIDAQAB
""".lstrip())

# Delete _deleted and deprecated slice attributes and types
for attribute_type in GetSliceTagTypes():
    id = attribute_type['attribute_type_id']
    name = attribute_type['name']

    if name == 'general_prop_share' or \
       re.match('nm_', name) or \
       re.search('_deleted$', name):
        DeleteSliceTagType(id)
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
        AddSliceTag(slice, 'proper_op', op)
    except Exception as err:
        print("Warning: %s:" % slice, err)

initscripts = dict([(initscript['initscript_id'], initscript) for initscript in [{'initscript_id': 8, 'script': 'IyEgL2Jpbi9zaA0KDQojIDxQcm9ncmFtIE5hbWU+DQojICAgIGJpbmRzY3JpcHQNCiMNCiMgPEF1dGhvcj4NCiMgICAgSmVmZnJ5IEpvaG5zdG9uIGFuZCBKZXJlbXkgUGxpY2h0YQ0KIw0KIyA8UHVycG9zZT4NCiMgICAgRG93bmxvYWRzIGFuZCBpbnN0YWxscyBzdG9yayBvbiBhIG5vZGUuDQoNCiMgc2F2ZSBvcmlnaW5hbCBQV0QNCk9MRFBXRD0kUFdEDQoNCiMgZXJyb3IgcmVwb3J0aW5nIGZ1bmN0aW9uDQplcnJvcigpDQp7DQogICBlY2hvDQogICBlY2hvICJQbGVhc2UgRS1tYWlsIHN0b3JrLXN1cHBvcnRAY3MuYXJpem9uYS5lZHUgaWYgeW91IGJlbGlldmUgeW91IGhhdmUiIA0KICAgZWNobyAicmVjZWl2ZWQgdGhpcyBtZXNzYWdlIGluIGVycm9yLiINCg0KICAgIyBnZXQgcmlkIG9mIENFUlQgZmlsZQ0KICAgaWYgWyAtZiAkQ0VSVCBdDQogICB0aGVuDQogICAgICBybSAtZiAkQ0VSVCA+IC9kZXYvbnVsbA0KICAgZmkNCg0KICAgIyByZXN0b3JlIG9yaWdpbmFsIFBXRA0KICAgY2QgJE9MRFBXRA0KICAgZXhpdCAxDQp9DQoNCkNFUlQ9YHB3ZGAvdGVtcGNydGZpbGUNCg0KI2Z1bmN0aW9ucw0KDQojIyMNCiMjIyBjcmVhdGVDZXJ0aWZpY2F0ZSgpDQojIyMgICAgcHJpbnRzIG91dCB0aGUgZXF1aWZheCBjZXJ0aWZpY2F0ZSB0byB1c2UgYW5kIHN0b3Jlcw0KIyMjICAgIHRoZSBmaWxlIG5hbWUgaW4gJENFUlQNCiMjIw0KZnVuY3Rpb24gY3JlYXRlQ2VydGlmaWNhdGUoKXsNCmNhdCA+ICRDRVJUIDw8RVFVSUZBWA0KLS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tDQpNSUlDa0RDQ0FmbWdBd0lCQWdJQkFUQU5CZ2txaGtpRzl3MEJBUVFGQURCYU1Rc3dDUVlEVlFRR0V3SlYNClV6RWNNQm9HQTFVRUNoTVRSWEYxYVdaaGVDQlRaV04xY21VZ1NXNWpMakV0TUNzR0ExVUVBeE1rUlhGMQ0KYVdaaGVDQlRaV04xY21VZ1IyeHZZbUZzSUdWQ2RYTnBibVZ6Y3lCRFFTMHhNQjRYRFRrNU1EWXlNVEEwDQpNREF3TUZvWERUSXdNRFl5TVRBME1EQXdNRm93V2pFTE1Ba0dBMVVFQmhNQ1ZWTXhIREFhQmdOVkJBb1QNCkUwVnhkV2xtWVhnZ1UyVmpkWEpsSUVsdVl5NHhMVEFyQmdOVkJBTVRKRVZ4ZFdsbVlYZ2dVMlZqZFhKbA0KSUVkc2IySmhiQ0JsUW5WemFXNWxjM01nUTBFdE1UQ0JuekFOQmdrcWhraUc5dzBCQVFFRkFBT0JqUUF3DQpnWWtDZ1lFQXV1Y1hrQUpsc1RSVlBFbkNVZFhmcDlFM2o5SG5nWE5CVW1DYm5hRVhKbml0eDdIb0pwUXkNCnRkNHpqVG92Mi9LYWVscHptS05jNmZ1S2N4dGM1OE8vZ0d6TnFmVFdLOEQzK1ptcVk2S3hSd0lQMU9SUg0KT2hJOGJJcGFWSVJ3MjhIRmtNOXlSY3VvV2NETk01MC9vNWJyaFRNaEhENGVQbUJ1ZHB4bmhjWEl3MkVDDQpBd0VBQWFObU1HUXdFUVlKWUlaSUFZYjRRZ0VCQkFRREFnQUhNQThHQTFVZEV3RUIvd1FGTUFNQkFmOHcNCkh3WURWUjBqQkJnd0ZvQVV2cWlnZEhKUWEwUzN5U1BZKzZqL3MxZHJhR3d3SFFZRFZSME9CQllFRkw2bw0Kb0hSeVVHdEV0OGtqMlB1by83TlhhMmhzTUEwR0NTcUdTSWIzRFFFQkJBVUFBNEdCQUREaUFWR3F4K3BmDQoycm5RWlE4dzFqN2FEUlJKYnBHVEp4UXg3OFQzTFVYNDdNZS9va0VOSTdTUytSa0FaNzBCcjgzZ2NmeGENCnoyVEU0SmFZMEtOQTRnR0s3eWNIOFdVQmlrUXRCbVYxVXNDR0VDQWhYMnhyRDJ5dUNSeXY4cUlZTk1SMQ0KcEhNYzhZM2M3NjM1czNhMGtyL2NsUkFldnN2SU8xcUVZQmxXbEtsVg0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLSANCkVRVUlGQVgNCn0NCg0KIyMjDQojIyMgb3ZlcldyaXRlQ29uZigpDQojIyMJb3ZlcndyaXRlIHRoZSBkZWZhdWx0IHN0b3JrLmNvbmYgZmlsZQ0KIyMjICAgICB0aGF0IHdhcyBpbnN0YWxsZWQgYnkgdGhlIHJwbSBwYWNrYWdlLg0KIyMjICAgICB0aGlzIGlzIGEgdGVtcG9yYXJ5IGhhY2sgYmVjYXVzZSBJIG5lZWQNCiMjIyAgICAgdG8gY2hhbmdlIHRoZSBuZXN0cG9ydCBhbmQgSSBkb250IGtub3cNCiMjIyAgICAgZW5vdWdoIHRvIHJlcGFja2FnZSB0aGUgcnBtIHdpdGggdGhlDQojIyMgICAgIGNvcnJlY3Qgc2V0dGluZ3MNCmZ1bmN0aW9uIG92ZXJXcml0ZUNvbmYoKXsNCmNhdCA+IC91c3IvbG9jYWwvc3RvcmsvZXRjL3N0b3JrLmNvbmYgPDxFTkRPRkZJTEUNCnBhY21hbj0vdXNyL2xvY2FsL3N0b3JrL2Jpbi9wYWNtYW4NCmR0ZC1wYWNrYWdlcz0vdXNyL2xvY2FsL3N0b3JrL2Jpbi9wYWNrYWdlcy5kdGQNCmR0ZC1ncm91cHM9L3Vzci9sb2NhbC9zdG9yay9iaW4vZ3JvdXBzLmR0ZA0Kc3RvcmtuZXN0dXBkYXRlbGlzdGVuZXJwb3J0PTY0OQ0KDQojYml0dG9ycmVudHRyYWNrZXJob3N0PXF1YWRydXMuY3MuYXJpem9uYS5lZHUNCmJpdHRvcnJlbnR0cmFja2VyaG9zdD1ucjA2LmNzLmFyaXpvbmEuZWR1DQoNCmJpdHRvcnJlbnR0cmFja2VycG9ydD02ODgwDQpiaXR0b3JyZW50dXBsb2FkcmF0ZT0wDQpiaXR0b3JyZW50c2VlZGxvb2t1cHRpbWVvdXQ9MzANCg0KI3BhY2thZ2VyZXBvc2l0b3J5ID0gcXVhZHJ1cy5jcy5hcml6b25hLmVkdS9QbGFuZXRMYWIvVjN8ZGlzdCwgc3RhYmxlDQpwYWNrYWdlcmVwb3NpdG9yeSA9IG5yMDYuY3MuYXJpem9uYS5lZHUvUGxhbmV0TGFiL1YzfGRpc3QsIHN0YWJsZQ0KI3BhY2thZ2VpbmZvcmVwb3NpdG9yeSA9IHF1YWRydXMuY3MuYXJpem9uYS5lZHUvUGxhbmV0TGFiL1YzL3N0b3JrLmluZm8NCnBhY2thZ2VpbmZvcmVwb3NpdG9yeSA9IG5yMDYuY3MuYXJpem9uYS5lZHUvUGxhbmV0TGFiL1YzL3N0b3JrLmluZm8NCg0KdXNlcm5hbWUgPSBQbGFuZXRMYWINCnB1YmxpY2tleWZpbGUgPSAvdXNyL2xvY2FsL3N0b3JrL3Zhci9rZXlzL1BsYW5ldExhYi5wdWJsaWNrZXkNCnBhY2thZ2VtYW5hZ2VycyA9IG5lc3RycG0sIHJwbSwgdGFyZ3oNCnRyYW5zZmVybWV0aG9kPSBuZXN0LGJpdHRvcnJlbnQsY29ibGl0eixjb3JhbCxodHRwLGZ0cA0KbmVzdHBvcnQ9NjAwMA0KdGFycGFja2luZm9wYXRoPS91c3IvbG9jYWwvc3RvcmsvdmFyL3RhcmluZm8NCkVORE9GRklMRQ0KfSANCg0KDQojIyMNCiMjIyBkb3dubG9hZE5SMDYoKQ0KIyMjICAgIGRvd25sb2FkIGEgZmlsZSBmcm9tIG5yMDYgdXNpbmcgY3VybA0KIyMjDQojIyMgYXJnczogDQojIyMgICAgICAgLSB0aGUgcGF0aCBvZiB0aGUgZmlsZSB5b3Ugd2lzaCB0byBkb3dubG9hZA0KIyMjICAgICAgICAgcmVsYXRpdmUgZnJvbSBodHRwczovL25yMDYuY3MuYXJpem9uYS5lZHUNCiMjIyAgICAgICAtIHRoZSBmaWxlIHRvIHNhdmUgaXQgdG8NCiMjIyAgICAgICAtIHJldHVybmVkIHZhbHVlIGFzIHNwZWNpZmllZCBpbiB2ZXJpZnlEb3dubG9hZA0KZnVuY3Rpb24gZG93bmxvYWROUjA2KCl7DQogICAgY3VybCAtLWNhY2VydCAkQ0VSVCBodHRwczovL25yMDYuY3MuYXJpem9uYS5lZHUvJDEgLW8gJDIgMj4vZGV2L251bGwNCiAgICB2ZXJpZnlEb3dubG9hZCAkMiAkMw0KfQ0KDQojIyMNCiMjIyB2ZXJpZnlEb3dubG9hZCgpDQojIyMgICAgIHZlcmlmeSB0aGF0IGEgZmlsZSB0aGF0IHdhcyBqdXN0IGRvd25sb2FkIHdpdGggZG93bmxvYWROUjA2DQojIyMgICAgIHdhcyBkb3dubG9hZCBjb3JyZWN0bHkuIFNpbmNlIHdlIGFyZSBnZXR0aW5nIHN0dWZmIGZyb20gYQ0KIyMjICAgICBodHRwIHNlcnZlciB3ZSBhcmUgYXNzdW1pbmcgdGhhdCBpZiB3ZSBnZXQgYSA0MDQgcmVzcG9uc2UNCiMjIyAgICAgdGhhdCB0aGUgcGFnZSB3ZSB3YW50IGRvZXMgbm90IGV4aXN0LiBBbHNvLCBpZiB0aGUgb3V0cHV0IGZpbGUNCiMjIyAgICAgZG9lcyBub3QgZXhpc3QgdGhhdCBtZWFucyB0aGF0IG9ubHkgaGVhZGVycyB3ZXJlIHJldHVybmVkDQojIyMgICAgIHdpdGhvdXQgYW55IGNvbnRlbnQuIHRoaXMgdG9vIGlzIGEgaW52YWxpZCBmaWxlIGRvd25sb2FkDQojIyMNCiMjIyBhcmdzOg0KIyMjICAgICAgIC0gdGhlIGZpbGUgdG8gdmVyaWZ5DQojIyMgICAgICAgLSByZXR1cm4gdmFyaWFibGUsIHdpbGwgaGF2ZSAxIGlmIGZhaWwgMCBpZiBnb29kDQojIyMNCmZ1bmN0aW9uIHZlcmlmeURvd25sb2FkKCl7DQogICAgZXZhbCAiJDI9MCINCiAgICBpZiBbICEgLWYgJDEgXTsNCiAgICB0aGVuDQogICAgICAgIGV2YWwgIiQyPTEiDQogICAgZWxpZiBncmVwICc0MDQgTm90IEZvdW5kJyAkMSA+IC9kZXYvbnVsbA0KICAgIHRoZW4NCglybSAtZiAkMQ0KICAgICAgICBldmFsICIkMj0xIg0KICAgIGVsc2UNCiAgICAgICAgZXZhbCAiJDI9MCINCiAgICBmaQ0KfQ0KDQoNCiMgY2hlY2sgZm9yIHJvb3QgdXNlcg0KaWYgWyAkVUlEIC1uZSAiMCIgXQ0KdGhlbg0KICAgZWNobyAiWW91IG11c3QgcnVuIHRoaXMgcHJvZ3JhbSB3aXRoIHJvb3QgcGVybWlzc2lvbnMuLi4iDQogICBlcnJvcg0KZmkgICANCiANCiMgY2xlYW4gdXAgaW4gY2FzZSB0aGlzIHNjcmlwdCB3YXMgcnVuIGJlZm9yZSBhbmQgZmFpbGVkDQpybSAtcmYgL3RtcC9zdG9yayAmPiAvZGV2L251bGwNCg0KIyBjcmVhdGUgL3RtcC9zdG9yayBkaXJlY3RvcnkNCm1rZGlyIC90bXAvc3RvcmsgDQppZiBbICQ/IC1uZSAiMCIgXQ0KdGhlbg0KICAgZWNobw0KICAgZWNobyAiQ291bGQgbm90IGNyZWF0ZSB0aGUgL3RtcC9zdG9yayBkaXJlY3RvcnkuLi4iDQogICBlcnJvcg0KZmkNCg0KIyBleHBvcnQgb3VyIHJvb3QgZGlyZWN0b3J5IHRvIFN0b3JrDQplY2hvICJhcml6b25hX3N0b3JrMiIgPiAvLmV4cG9ydGRpcg0KaWYgWyAkPyAtbmUgIjAiIF0NCnRoZW4NCiAgIGVjaG8NCiAgIGVjaG8gIkNvdWxkIG5vdCBjcmVhdGUgdGhlIC8uZXhwb3J0ZGlyIGZpbGUuLi4iDQogICBlcnJvcg0KZmkNCiANCiMgdGVsbCBzdG9yayB0aGF0IHdlIHdhbnQgdG8gYmUgc2VydmVkDQppZiBbIC1mIC9ldGMvc2xpY2VuYW1lIF0NCnRoZW4NCiAgIFNMSUNFTkFNRT1gY2F0IC9ldGMvc2xpY2VuYW1lYA0KZWxzZSANCiAgIFNMSUNFTkFNRT0kVVNFUg0KZmkNCndnZXQgLU8gL3RtcC9zdG9yay8kU0xJQ0VOQU1FICJodHRwOi8vbG9jYWxob3N0OjY0OC8kU0xJQ0VOQU1FXCRiaW5kc2NyaXB0Ig0KDQojIHZlcmlmeSB0aGF0IHRoZSBkb3dubG9hZCB3YXMgc3VjY2Vzc2Z1bA0KaWYgWyAhIC1mIC90bXAvc3RvcmsvJFNMSUNFTkFNRSAtbyAkPyAtbmUgMCBdDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJTdG9yayBkb2Vzbid0IHNlZW0gdG8gYmUgcnVubmluZyBvbiB0aGlzIG5vZGUuLi4iDQogICBlcnJvcg0KZmkNCg0KIyB3YWl0IGZvciBzdG9yayBzbGljZSANCmVjaG8gIldhaXRpbmcgZm9yIFN0b3JrIHRvIGFjY2VwdCBvdXIgYmluZGluZy4uLiINCndoaWxlIFsgISAtZiAvdG1wL3N0b3JrL3N0b3JrX3NheXNfZ28gXQ0KZG8NCiAgIHNsZWVwIDENCmRvbmUNCg0KIyBjaGFuZ2UgUFdEIHRvIHRoZSAvdG1wL3N0b3JrIGRpcmVjdG9yeSANCmNkIC90bXAvc3RvcmsNCmlmIFsgJD8gLW5lICIwIiBdDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJDb3VsZCBub3QgYWNjZXNzIHRoZSAvdG1wL3N0b3JrIGRpcmVjdG9yeS4uLiINCiAgIGVycm9yDQpmaQ0KDQojIGNvbmZpcm0gdGhhdCBwYWNrYWdlcyB0byBiZSBpbnN0YWxsZWQgYWN0dWFsbHkgZXhpc3QNCmlmIGVjaG8gKi5ycG0gfCBncmVwICcqJyA+IC9kZXYvbnVsbA0KdGhlbg0KICAgZWNobw0KICAgZWNobyAiRXJyb3I6IFN0b3JrIHBhY2thZ2UgZG93bmxvYWQgZmFpbGVkLi4uIg0KICAgZXJyb3INCmZpDQoNCiMgcmVtb3ZlIFN0b3JrIHBhY2thZ2VzIGFuZCBmaWxlcw0KZWNobw0KZWNobyAiUmVtb3ZpbmcgU3RvcmsgZmlsZXMuLi4iDQoNCiMgYnVpbGQgYSBsaXN0IG9mIHBhY2thZ2VzIHRvIHJlbW92ZQ0KcGFja2FnZXM9IiINCmZvciBmaWxlbmFtZSBpbiAqLnJwbQ0KZG8NCiAgIyBjb252ZXJ0IGZpbGVuYW1lIHRvIGEgcGFja2FnZSBuYW1lDQogIHBhY2s9YHJwbSAtcXAgLS1xZiAiJXtOQU1FfVxuIiAkZmlsZW5hbWVgDQogIGlmIFsgJD8gLWVxICIwIiBdDQogIHRoZW4NCiAgICBwYWNrYWdlcz0iJHBhY2thZ2VzICRwYWNrIg0KICBmaQ0KZG9uZSAgIA0KDQojIHJlbW92ZSBvbGQgU3RvcmsgcGFja2FnZXMNCnJwbSAtZSAkcGFja2FnZXMgJj4gL2Rldi9udWxsDQoNCiMgcmVtb3ZlIGFueXRoaW5nIGxlZnQgaW4gL3Vzci9sb2NhbC9zdG9yay9iaW4NCnJtIC1yZiAvdXNyL2xvY2FsL3N0b3JrL2Jpbi8qICY+IC9kZXYvbnVsbCANCg0KIyBpbnN0YWxsIFN0b3JrIHBhY2thZ2VzDQplY2hvDQplY2hvICJJbnN0YWxsaW5nIHBhY2thZ2VzLi4uIiANCg0KIyBidWlsZCBhIGxpc3Qgb2YgcGFja2FnZXMgdG8gaW5zdGFsbA0KcGFja2FnZXM9IiINCmZvciBmaWxlbmFtZSBpbiAqLnJwbQ0KZG8NCiAgcGFja2FnZXM9IiRwYWNrYWdlcyAkZmlsZW5hbWUiDQpkb25lICAgDQoNCiMgaW5zdGFsbCB0aGUgbmV3IHN0b3JrIHBhY2thZ2VzDQpycG0gLWkgJHBhY2thZ2VzDQoNCiMgcmVwb3J0IHBhY2thZ2UgaW5zdGFsbGF0aW9uIGVycm9ycw0KaWYgWyAkPyAtbmUgIjAiIF0NCnRoZW4NCiAgZWNobyAiV2FybmluZzogUG9zc2libGUgZXJyb3IgaW5zdGFsbGluZyBTdG9yayBwYWNrYWdlcy4uLiINCmZpDQoNCiMgcmVzdG9yZSBvcmlnaW5hbCBQV0QNCmNkICRPTERQV0QNCg0KIyBjbGVhbiB1cCB0ZW1wb3JhcnkgZmlsZXMNCnJtIC1yZiAvdG1wL3N0b3JrICY+IC9kZXYvbnVsbA0KDQojIFNFRSBUTy1ETyAxDQojY3JlYXRlIHRoZSBlcXVpZmF4IGNlcnRpZmljYXRlIHRvIHVzZSBmb3IgY3VybA0KI2NyZWF0ZUNlcnRpZmljYXRlDQoNCiMgVE8tRE8gMQ0KIyBpbXBsZW1lbnQgdGhlIGJlbG93IGluIHRoZSBiZWdnaW5pbmcgb2Ygc3RvcmsucHkNCiNhdHRlbXB0IHRvIGRvd25sb2FkIHRoZSB1c2VycyBwdWJsaWMga2V5IGZyb20gdGhlIHJlcG9zaXRvcnkNCiNkb3dubG9hZE5SMDYgInVzZXItdXBsb2FkL3B1YmtleXMvJFNMSUNFTkFNRS5wdWJsaWNrZXkiICIvdXNyL2xvY2FsL3N0b3JrL3Zhci8kU0xJQ0VOQU1FLnB1YmxpY2tleSIgUkVUDQoNCiNpZiBbICRSRVQgLW5lIDAgXTsNCiN0aGVuDQojICAgZWNobw0KIyAgIGVjaG8gIkNvdWxkIG5vdCBmZXRjaCB5b3VyIHB1YmxpYyBrZXkgZnJvbSB0aGUgcmVwb3NpdG9yeS4iDQojICAgZWNobyAiSWYgeW91IHdhbnQgdG8gdXBsb2FkIG9uZSBmb3IgdGhlIG5leHQgdGltZSB5b3UgcnVuIg0KIyAgIGVjaG8gInRoZSBpbml0c2NyaXB0IHBsZWFzZSB2aXNpdCINCiMgICBlY2hvICJodHRwOi8vbnIwNi5jcy5hcml6b25hLmVkdS90ZXN0cGhwL3VwbG9hZC5waHAiDQojICAgZWNobw0KI2ZpDQoNCiNhdHRlbXB0IHRvIGRvd25sb2FkIHRoZSB1c2VycyBzdG9yay5jb25mIGZpbGUgZnJvbSB0aGUgcmVwb3NpdG9yeQ0KI2Rvd25sb2FkTlIwNiAidXNlci11cGxvYWQvY29uZi8kU0xJQ0VOQU1FLnN0b3JrLmNvbmYiICIvdXNyL2xvY2FsL3N0b3JrL2V0Yy9zdG9yay5jb25mLnVzZXJzIiBSRVQNCg0KI2lmIFsgJFJFVCAtbmUgMCBdOw0KI3RoZW4NCiMgICBlY2hvDQojICAgZWNobyAiQ291bGQgbm90IGZldGNoIHlvdXIgc3RvcmsuY29uZiBmaWxlIGZyb20gdGhlIHJlcG9zaXRvcnkuIg0KIyAgIGVjaG8gIklmIHlvdSB3YW50IHRvIHVwbG9hZCBvbmUgZm9yIHRoZSBuZXh0IHRpbWUgeW91IHJ1biINCiMgICBlY2hvICJ0aGUgaW5pdHNjcmlwdCBwbGVhc2UgdmlzaXQiDQojICAgZWNobyAiaHR0cDovL25yMDYuY3MuYXJpem9uYS5lZHUvdGVzdHBocC91cGxvYWQucGhwIg0KIyAgIGVjaG8gIlN0b3JrIHdpbGwgd29yayB3aXRob3V0IGEgY29uZmlndXJhdGlvbiBmaWxlIGJ1dCB0byBtYWtlIG9uZSINCiMgICBlY2hvICJwbGVhc2UgcGxhY2UgYSBmaWxlIG5hbWVkIHN0b3JrLmNvbmYgaW4gL3Vzci9sb2NhbC9zdG9yay9ldGMiDQojICAgZWNobyAicmVmZXIgdG8gdGhlIG1hbnVhbCBmb3IgbW9yZSBkaXJlY3Rpb25zIG9yIGVtYWlsOiINCiMgICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhZGRpdGlvbmFsIGFzc2lzdGFuY2UuIg0KIyAgIGVjaG8NCiNmaQ0KDQojZG9udCBuZWVkIHRvIG92ZXJ3cml0ZSB0aGUgZGVmYXVsdCBjb25mIGZpbGUNCiNiZWNhdXNlIGl0IHNob3VsZCBiZSBmaXhlZCBpbiB0aGUgbmV3IHJwbXMNCiNvdmVyV3JpdGVDb25mDQoNCiMgcnVuIHN0b3JrIHRvIHVwZGF0ZSBrZXlmaWxlcyBhbmQgZG93bmxvYWQgcGFja2FnZSBsaXN0cw0KZWNobw0KZWNobyAiQXR0ZW1wdGluZyB0byBjb21tdW5pY2F0ZSB3aXRoIHN0b3JrLi4uIg0KaWYgc3RvcmsgDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJDb25ncmF0dWxhdGlvbnMsIHlvdSBoYXZlIHN1Y2Nlc3NmdWxseSBib3VuZCB0byBzdG9yayEiDQogICBlY2hvDQogICBlY2hvICJGb3IgaGVscCwgeW91IG1heSB0eXBlIHN0b3JrIC0taGVscCINCiAgIGVjaG8NCiAgICNlY2hvICJUaGVyZSBpcyBhbHNvIGEgc3RvcmtxdWVyeSBjb21tYW5kIHRoYXQgd2lsbCBwcm92aWRlIGluZm9ybWF0aW9uIg0KICAgI2VjaG8gImFib3V0IHBhY2thZ2VzIGluIHRoZSByZXBvc2l0b3J5LiINCiAgIGVjaG8NCiAgIGVjaG8gIkZvciBtb3JlIGhlbHAsIHZpc2l0IHRoZSBzdG9yayBwcm9qZWN0IG9ubGluZSBhdCINCiAgIGVjaG8gImh0dHA6Ly93d3cuY3MuYXJpem9uYS5lZHUvc3RvcmsvLiAgUGxlYXNlIGNvbnRhY3QiDQogICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhZGRpdGlvbmFsIGFzc2lzdGFuY2UuIiANCiAgICNybSAtZiAkQ0VSVCA+IC9kZXYvbnVsbA0KZWxzZQ0KICAgZWNobw0KICAgZWNobyAiQW4gZXJyb3Igb2NjdXJyZWQgZHVyaW5nIGluc3RhbGwgZmluYWxpemF0aW9uLi4uICBQbGVhc2UgY29udGFjdCINCiAgIGVjaG8gInN0b3JrLXN1cHBvcnRAY3MuYXJpem9uYS5lZHUgZm9yIGFzc2lzdGFuY2UuIg0KICAgI3JtIC1mICRDRVJUID4gL2Rldi9udWxsDQogICBleGl0IDENCmZpDQoNCiMgZG9uZQ0KZXhpdCAwDQo=', 'name': 'arizona_stork_2', 'encoding': 'base64'}, {'initscript_id': 9, 'script': 'IyEvYmluL2Jhc2gNCmNkIC8NCnJtIC1mIHN0YXJ0X3B1cnBsZQ0Kd2dldCBodHRwOi8vd3d3LmNzLnByaW5jZXRvbi5lZHUvfmRlaXNlbnN0L3B1cnBsZS9zdGFydF9wdXJwbGUNCmNobW9kIDc1NSBzdGFydF9wdXJwbGUNCnN1IHByaW5jZXRvbl9wdXJwbGUgLWMgJy4vc3RhcnRfcHVycGxlJw0K', 'name': 'princeton_purple', 'encoding': 'base64'}, {'initscript_id': 6, 'script': 'IyEgL2Jpbi9zaA0KDQojIHNhdmUgb3JpZ2luYWwgUFdEDQpPTERQV0Q9JFBXRA0KDQojIGVycm9yIHJlcG9ydGluZyBmdW5jdGlvbg0KZXJyb3IoKQ0Kew0KICAgZWNobw0KICAgZWNobyAiUGxlYXNlIEUtbWFpbCBzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGlmIHlvdSBiZWxpZXZlIHlvdSBoYXZlIiANCiAgIGVjaG8gInJlY2VpdmVkIHRoaXMgbWVzc2FnZSBpbiBlcnJvci4iDQoNCiAgICMgcmVzdG9yZSBvcmlnaW5hbCBQV0QNCiAgIGNkICRPTERQV0QNCiAgIGV4aXQgMQ0KfQ0KDQojIGNoZWNrIGZvciByb290IHVzZXINCmlmIFsgJFVJRCAtbmUgIjAiIF0NCnRoZW4NCiAgIGVjaG8gJ1lvdSBtdXN0IGJlIHJvb3QgdG8gcnVuIHRoaXMgcHJvZ3JhbS4uLicNCiAgIGVycm9yDQpmaSAgIA0KIA0KIyBDbGVhbiB1cCBpbiBjYXNlIEkgcmFuIHRoaXMgYmVmb3JlDQpybSAtZiAvdG1wL3N0b3JrKiA+IC9kZXYvbnVsbCAyPiYxDQoNCiMgRmlyc3Qgb2YgYWxsIGV4cG9ydCBvdXIgcm9vdCBkaXJlY3RvcnkgdG8gU3RvcmsNCmVjaG8gImFyaXpvbmFfc3RvcmsiID4gLy5leHBvcnRkaXINCiANCiMgTm93IHRlbGwgc3RvcmsgdGhhdCB3ZSB3YW50IHRvIGJlIHNlcnZlZA0KaWYgWyAtZiAvZXRjL3NsaWNlbmFtZSBdDQp0aGVuDQogICBTTElDRU5BTUU9YGNhdCAvZXRjL3NsaWNlbmFtZWANCmVsc2UgDQogICBTTElDRU5BTUU9JFVTRVINCmZpDQoNCndnZXQgaHR0cDovL2xvY2FsaG9zdDo2NDAvJFNMSUNFTkFNRQ0KDQojIGNoZWNrIHRvIG1ha2Ugc3VyZSB0aGUgZG93bmxvYWQgd2FzIHN1Y2Nlc3NmdWwNCmlmIFsgISAtZiAkU0xJQ0VOQU1FIC1vICQ/IC1uZSAwIF0NCnRoZW4NCiAgIGVjaG8NCiAgIGVjaG8gIlN0b3JrIGRvZXNuJ3Qgc2VlbSB0byBiZSBydW5uaW5nIG9uIHRoaXMgbm9kZS4uLiINCiAgIGVycm9yDQpmaQ0KDQojIHdhaXQgZm9yIHN0b3JrIHNsaWNlIA0KZWNobyAiV2FpdGluZyBmb3IgU3RvcmsgdG8gYWNjZXB0IG91ciBiaW5kaW5nLi4uIg0Kd2hpbGUgWyAhIC1mIC90bXAvc3Rvcmtfc2F5c19nbyBdDQpkbw0KICAgc2xlZXAgMQ0KZG9uZQ0KDQojIGNoYW5nZSBQV0QgdG8gdGhlIC90bXAgZGlyZWN0b3J5IA0KY2QgL3RtcA0KaWYgWyAkPyAtbmUgIjAiIF0NCnRoZW4NCiAgIGVjaG8NCiAgIGVjaG8gIkNvdWxkIG5vdCBhY2Nlc3MgdGhlIC90bXAgZGlyZWN0b3J5Li4uIg0KICAgZXJyb3INCmZpDQoNCiMgY29uZmlybSB0aGF0IHBhY2thZ2VzIHRvIGJlIGluc3RhbGxlZCBhY3R1YWxseSBleGlzdA0KaWYgZWNobyAqLnJwbSB8IGdyZXAgJyonID4gL2Rldi9udWxsDQp0aGVuDQogICBlY2hvDQogICBlY2hvICJFcnJvcjogU3RvcmsgcGFja2FnZSBkb3dubG9hZCBmYWlsZWQuLi4iDQogICBlcnJvcg0KZmkNCg0KIyBpbnN0YWxsIFN0b3JrIHBhY2thZ2VzDQplY2hvICJJbnN0YWxsaW5nIHBhY2thZ2VzLi4uIiANCmZvciBwYWNrIGluICoucnBtDQpkbw0KICAgIyByZW1vdmUgdGhlIG9sZCBzdG9yayBwYWNrYWdlLCBpZiBhbnkNCiAgIHJwbSAtZSBgcnBtIC1xcCAtLXFmICIle05BTUV9XG4iICRwYWNrYCA+IC9kZXYvbnVsbCAyPiYxDQoNCiAgICMgcmVtb3ZlIGFueXRoaW5nIGxlZnQgaW4gL3Vzci9sb2NhbC9zdG9yay9iaW4NCiAgIHJtIC1yZiAvdXNyL2xvY2FsL3N0b3JrL2Jpbi8qID4gL2Rldi9udWxsIDI+JjENCg0KICAgIyBpbnN0YWxsIHRoZSBuZXcgc3RvcmsgcGFja2FnZQ0KICAgcnBtIC1pICRwYWNrDQoNCiAgICMgcmVwb3J0IHBhY2thZ2UgaW5zdGFsbGF0aW9uIGVycm9ycw0KICAgaWYgWyAkPyAtbmUgIjAiIF0NCiAgIHRoZW4NCiAgICAgZWNobyAiV2FybmluZzogUG9zc2libGUgZXJyb3IgaW5zdGFsbGluZyBTdG9yayBwYWNrYWdlOiAkcGFjay4uLiINCiAgIGZpDQpkb25lDQoNCiMgcmVzdG9yZSBvcmlnaW5hbCBQV0QNCmNkICRPTERQV0QNCg0KIyBjbGVhbiB1cCB0ZW1wb3JhcnkgZmlsZXMNCnJtIC1mIC90bXAvc3RvcmsqID4gL2Rldi9udWxsIDI+JjENCnJtICRTTElDRU5BTUUqIA0KDQojIHJ1biBzdG9yayB0byB1cGRhdGUga2V5ZmlsZXMgYW5kIGRvd25sb2FkIHBhY2thZ2UgbGlzdHMNCmVjaG8gIkF0dGVtcHRpbmcgdG8gY29tbXVuaWNhdGUgd2l0aCBzdG9yay4uLiINCmlmIHN0b3JrIA0KdGhlbg0KICAgZWNobw0KICAgZWNobyAiQ29uZ3JhdHVsYXRpb25zLCB5b3UgaGF2ZSBzdWNjZXNzZnVsbHkgYm91bmQgdG8gc3RvcmshIg0KICAgZWNobw0KICAgZWNobyAiRm9yIGhlbHAsIHlvdSBtYXkgdHlwZSBzdG9yayAtLWhlbHAgIg0KICAgZWNobw0KICAgZWNobyAiVGhlcmUgaXMgYWxzbyBhIHN0b3JrcXVlcnkgY29tbWFuZCB0aGF0IHdpbGwgcHJvdmlkZSBpbmZvcm1hdGlvbiINCiAgIGVjaG8gImFib3V0IHBhY2thZ2VzIGluIHRoZSByZXBvc2l0b3J5LiINCiAgIGVjaG8NCiAgIGVjaG8gIkZvciBtb3JlIGhlbHAsIHZpc2l0IHRoZSBzdG9yayBwcm9qZWN0IG9ubGluZSBhdCINCiAgIGVjaG8gImh0dHA6Ly93d3cuY3MuYXJpem9uYS5lZHUvc3RvcmsvLiAgUGxlYXNlIGNvbnRhY3QiDQogICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhZGRpdGlvbmFsIGFzc2lzdGFuY2UuIiANCmVsc2UNCiAgIGVjaG8NCiAgIGVjaG8gIkFuIGVycm9yIG9jY3VycmVkIGR1cmluZyBpbnN0YWxsIGZpbmFsaXphdGlvbi4uLiAgUGxlYXNlIGNvbnRhY3QiDQogICBlY2hvICJzdG9yay1zdXBwb3J0QGNzLmFyaXpvbmEuZWR1IGZvciBhc3Npc3RhbmNlLiINCiAgIGV4aXQgMQ0KZmkNCg0KIw0KIyBIZWxsbyBXb3JsZCBkZW1vIGNvZGUNCiMNCg0KIyBQdWJsaWMga2V5IGZvciB0aGlzIGRlbW8NCmNhdCA+L3Vzci9sb2NhbC9zdG9yay92YXIva2V5cy9oZWxsby5wdWJsaWNrZXkgPDwiRU9GIg0KLS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0NCk1Gd3dEUVlKS29aSWh2Y05BUUVCQlFBRFN3QXdTQUpCQU1XcVE3K2VxQVljNlRPSUJPbkJyRnZqYjlnRVViaWgNCkkxd0Nyeld4a09aa01BcXFmY1RuMW9tcCtLMGd0cUtBK3VaNEIzRGlQRXI0Q0V0Myt5MmJlMGtDQXdFQUFRPT0NCi0tLS0tRU5EIFBVQkxJQyBLRVktLS0tLQ0KRU9GDQpzZWQgLWkgLWUgJ3MvXnVzZXJuYW1lLiovdXNlcm5hbWUgPSBoZWxsby8nIC91c3IvbG9jYWwvc3RvcmsvZXRjL3N0b3JrLmNvbmYNCg0KIyBJbnN0YWxsIFJQTQ0Kc3RvcmsgdXBncmFkZSBoZWxsbw0KDQojIGVuZA0KZXhpdCAwDQo=', 'name': 'princeton_hello_stork', 'encoding': 'base64'}, {'initscript_id': 10, 'script': 'IyEvYmluL2Jhc2gNCg0KIyBJbml0IHNjcmlwdCBmb3IgdGhlIFBsYW5ldExhYiAiSGVsbG8gV29ybGQiIGRlbW8gdXNpbmcgR29vZ2xlIEVhcnRoLg0KIyBJbnN0YWxscyBhIGNyb250YWIgZW50cnkgb24gdGhlIG5vZGUgdGhhdCBwaG9uZXMgaG9tZSB0byB0aGUgc2VydmVyDQojIGV2ZXJ5IHRocmVlIG1pbnV0ZXMuDQoNClNFUlZFUj0xMjguMTEyLjEzOS43Mzo4MDQyCQkjIHBsYW5ldGxhYi0zLmNzLnByaW5jZXRvbi5lZHUNCg0KL3Vzci9iaW4vY3VybCAtcyBodHRwOi8vJFNFUlZFUi8NCmVjaG8gIiovNSAqICogKiAqIC91c3IvYmluL2N1cmwgLXMgaHR0cDovLyRTRVJWRVIvIiB8IGNyb250YWIgLQ0KL3NiaW4vY2hrY29uZmlnIGNyb25kIG9uDQo=', 'name': 'princeton_hello', 'encoding': 'base64'}]])

# Convert plc_initscript.initscript_id to raw initscript attribute
for slice_attribute in GetSliceTags({'name': 'plc_initscript'}):
    id = slice_attribute['slice_attribute_id']
    slice_id = slice_attribute['slice_id']
    initscript_id = int(slice_attribute['value'])

    # Delete old attribute
    DeleteSliceTag(id)

    if initscript_id not in initscripts:
        print("Warning: Missing initscript %d" % initscript_id)
        continue

    initscript = base64.b64decode(initscripts[initscript_id]['script'])

    # Add as initscript attribute
    AddSliceTag(slice_id, 'initscript', initscript)

# Add our custom yum.conf entries
conf_file_id = AddConfFile({
    'enabled': True,
    'source': 'PlanetLabConf/yum.conf.php?gpgcheck=1&alpha',
    'dest': '/etc/yum.conf',
    'file_permissions': '644',
    'file_owner': 'root',
    'file_group': 'root',
    'preinstall_cmd': '',
    'postinstall_cmd': '',
    'error_cmd': '',
    'ignore_cmd_errors': False,
    'always_update': False})
AddConfFileToNodeGroup(conf_file_id, 'Alpha')

conf_file_id = AddConfFile({
    'enabled': True,
    'source': 'PlanetLabConf/yum.conf.php?gpgcheck=1&beta',
    'dest': '/etc/yum.conf',
    'file_permissions': '644',
    'file_owner': 'root',
    'file_group': 'root',
    'preinstall_cmd': '',
    'postinstall_cmd': '',
    'error_cmd': '',
    'ignore_cmd_errors': False,
    'always_update': False})
AddConfFileToNodeGroup(conf_file_id, 'Beta')

conf_file_id = AddConfFile({
    'enabled': True,
    'source': 'PlanetLabConf/yum.conf.php?gpgcheck=1&rollout',
    'dest': '/etc/yum.conf',
    'file_permissions': '644',
    'file_owner': 'root',
    'file_group': 'root',
    'preinstall_cmd': '',
    'postinstall_cmd': '',
    'error_cmd': '',
    'ignore_cmd_errors': False,
    'always_update': False})
AddConfFileToNodeGroup(conf_file_id, 'Rollout')

# Add OneLab as a peer
onelab = {'peername': 'OneLab', 'peer_url': 'https://onelab-plc.inria.fr/PLCAPI/', 'key': '-----BEGIN PGP PUBLIC KEY BLOCK-----\nVersion: GnuPG v1.4.5 (GNU/Linux)\n\nmQGiBEW0kJMRBACaTlrW0eYlQwkzRuMFfEYMwyqBT9Bm6R4g68SJ5GdjCRu3XCnd\nGTGCFF4ewOu6IcUmZDv39eqxShBWyx+JqBogYPGNvPrj07jXXKaSBCM7TPk+9kMW\nPziIxSClvO15XaPKv89c6kFaEBe0z1xsoMB/TNoLmhFUxmc24O7JnEqmYwCgjzIS\nHP7u9KIOYk1ZlTdOtwyRxVkD/1uYbPzD0Qigf8uF9ADzx7I4F1ATd2ezYq0EfzhD\nTDa15FPWwA7jm+Mye//ovT01Ju6JQtCU4N9wRsV2Yy2tWcWFZiYt+BISPVS0lJDx\nQ2Cd2+kEWyl9ByL9/ACHmCUz0OOaz9j1x+GpJLArjUdZSJOs68kPw90F62mrLHfg\nYCHpA/0ZcdJQG9QYNZ67KMFqNPho+uRww5/7kxQ4wkSyP7EK3QUVgXG5OWZ/1mPZ\njon9N04nnjrL9qoQv7m04ih3rmqyGy1MsicNCoys0RNh1eavPdAsXD1ZEXnWPA7z\naC37hxUaRPP3hH+1ifjPpAWQX1E89MK2y2zQpZipvEOAO2Lw8LRCT25lTGFiIENl\nbnRyYWwgKGh0dHA6Ly9vbmVsYWItcGxjLmlucmlhLmZyLykgPHN1cHBvcnRAb25l\nLWxhYi5vcmc+iGAEExECACAFAkW0kJMCGyMGCwkIBwMCBBUCCAMEFgIDAQIeAQIX\ngAAKCRBuu7E0vzFd9fvbAJ9QB2neTSbAN5HuoigIbuKzTUCTjQCeM/3h7/OmjD+z\n6yXtWD4Fzyfr7fSIYAQTEQIAIAUCRbibbAIbIwYLCQgHAwIEFQIIAwQWAgMBAh4B\nAheAAAoJEG67sTS/MV31w3AAn2t6qb94HIPmqCoD/ptK34Dv+VW0AJ4782ffPPnk\nbVXHU/Sx31QCoFmj34hgBBMRAgAgBQJFtJJBAhsjBgsJCAcDAgQVAggDBBYCAwEC\nHgECF4AACgkQbruxNL8xXfU5UQCeKqXWeNzTqdMqj/qHPkp1JCb+isEAn2AzDnde\nITF0aYd02RAKsU4sKePEtEJPbmVMYWIgQ2VudHJhbCAoaHR0cDovL29uZWxhYi1w\nbGMuaW5yaWEuZnIvKSA8c3VwcG9ydEBvbmUtbGFiLm9yZz6IYAQTEQIAIAUCRbi2\npgIbIwYLCQgHAwIEFQIIAwQWAgMBAh4BAheAAAoJEG67sTS/MV31W4AAn0rW5yjR\n2a8jPP/V44gw1JhqnE8jAKCMAEh0nPjvle5oLEGectC3Es9Pm7kBDQRFtJCUEAQA\nhp38fNVy/aJiPg2lUKKnA6KjrRm3LxD66N8MSWfxGCIYzQRJHhmZWnS+m1DDOjdu\nFG9FM6QrsCRRcEQuvhKI2ORFfK75D24lj4QaXzw7vfBbAibTaDsYa0b5LxfR5pGj\nYPCQ5LrRex+Ws3DrB3acJE5/XnYJZ+rUO1ZJlm00FTMAAwUD/Ai4ZUunVB8F0VqS\nhJgDYQF08/OlAnDAcbL//P5dtXdztUNSgXZM4wW/XFnDvAsBuRnbfkT/3BeptM9L\neEbdrMi4eThLstSl13ITOsZbSL3i/2OO9sPAxupWzRWOXcQILpqR2YMRK1EapO+M\nNhjrgxU9JpMXz24FESocczSyywDXiEkEGBECAAkFAkW0kJQCGwwACgkQbruxNL8x\nXfXGxQCfZqzSqinohParWaHv+4XNoIz2B7IAn2Ge0O5wjYZeV/joulkTXfPKm7Iu\n=SsZg\n-----END PGP PUBLIC KEY BLOCK-----\n', 'cacert': 'Certificate:\r\n    Data:\r\n        Version: 3 (0x2)\r\n        Serial Number: 67109883 (0x40003fb)\r\n        Signature Algorithm: sha1WithRSAEncryption\r\n        Issuer: C=US, O=GTE Corporation, OU=GTE CyberTrust Solutions, Inc., CN=G\r\n        Validity\r\n            Not Before: Mar 14 20:30:00 2006 GMT\r\n            Not After : Mar 14 23:59:00 2013 GMT\r\n        Subject: C=BE, O=Cybertrust, OU=Educational CA, CN=Cybertrust Educationa\r\n        Subject Public Key Info:\r\n            Public Key Algorithm: rsaEncryption\r\n            RSA Public Key: (2048 bit)\r\n                Modulus (2048 bit):\r\n                    00:95:22:a1:10:1d:4a:46:60:6e:05:91:9b:df:83:\r\n                    c2:ed:12:b2:5a:7c:f8:ab:e1:f8:50:5c:28:2c:7e:\r\n                    7e:00:38:93:b0:8b:4a:f1:c2:4c:3c:10:2c:3c:ef:\r\n                    b0:ec:a1:69:2f:b9:fc:cc:08:14:6b:8d:4f:18:f3:\r\n                    83:d2:fa:a9:37:08:20:aa:5c:aa:80:60:a2:d5:a5:\r\n                    22:00:cf:5a:e5:b4:97:df:ba:1e:be:5c:8e:17:19:\r\n                    66:fd:af:9f:7c:7b:89:b2:0e:24:d8:c7:ab:63:c4:\r\n                    95:32:8d:48:e6:63:59:7d:04:b8:33:a8:bd:d7:5d:\r\n                    64:bc:63:b5:f7:4d:28:fd:f9:06:72:31:5c:ba:45:\r\n                    94:65:a3:d2:b4:58:ec:3b:61:58:44:a3:2f:62:b3:\r\n                    9b:80:b4:82:fd:d5:c7:cc:51:25:e5:95:3f:47:2f:\r\n                    30:7b:ac:c8:78:6e:e2:e1:6d:27:eb:3d:cc:01:82:\r\n                    e8:35:77:8d:ab:58:bb:55:d1:d5:a4:81:56:8d:1c:\r\n                    d0:14:b1:b0:06:de:a0:91:22:f3:f0:a8:34:17:47:\r\n                    c6:e0:3e:f6:0c:5a:ac:7e:50:4b:cd:e1:69:6e:06:\r\n                    fc:06:7e:6a:4d:b4:95:99:a0:59:5c:35:66:ec:d9:\r\n                    49:d4:17:e0:60:b0:5d:a5:d7:1a:e2:2a:6e:66:f2:\r\n                    af:1d\r\n                Exponent: 65537 (0x10001)\r\n        X509v3 extensions:\r\n            X509v3 CRL Distribution Points: \r\n                URI:http://www.public-trust.com/cgi-bin/CRL/2018/cdp.crl\r\n\r\n            X509v3 Subject Key Identifier: \r\n                65:65:A3:3D:D7:3B:11:A3:0A:07:25:37:C9:42:4A:5B:76:77:50:E1\r\n            X509v3 Certificate Policies: \r\n                Policy: 1.3.6.1.4.1.6334.1.0\r\n                  CPS: http://www.public-trust.com/CPS/OmniRoot.html\r\n\r\n            X509v3 Authority Key Identifier: \r\n                DirName:/C=US/O=GTE Corporation/OU=GTE CyberTrust Solutions, Inc\r\n                serial:01:A5\r\n\r\n            X509v3 Key Usage: critical\r\n                Certificate Sign, CRL Sign\r\n            X509v3 Basic Constraints: critical\r\n                CA:TRUE, pathlen:0\r\n    Signature Algorithm: sha1WithRSAEncryption\r\n        43:b3:45:83:54:71:c4:1f:dc:b2:3c:6b:4e:bf:26:f2:4e:f2:\r\n        ad:9a:5b:fa:86:37:88:e8:14:6c:41:18:42:5f:ef:65:3e:eb:\r\n        03:77:a0:b7:9e:75:7a:51:7c:bb:15:5b:b8:af:91:a0:34:92:\r\n        53:ed:7f:2a:49:84:ac:b9:80:4b:b5:c7:b2:23:22:fb:eb:d8:\r\n        fb:6e:c9:3c:f3:d2:d1:bb:be:c9:1c:ff:6d:01:db:69:80:0e:\r\n        99:a5:ea:9e:7b:97:98:8f:b7:cf:22:9c:b3:b8:5d:e5:a9:33:\r\n        17:74:c6:97:37:0f:b4:e9:26:82:5f:61:0b:3f:1e:3d:64:e9:\r\n        2b:9b\r\n-----BEGIN CERTIFICATE-----\r\nMIIEQjCCA6ugAwIBAgIEBAAD+zANBgkqhkiG9w0BAQUFADB1MQswCQYDVQQGEwJV\r\nUzEYMBYGA1UEChMPR1RFIENvcnBvcmF0aW9uMScwJQYDVQQLEx5HVEUgQ3liZXJU\r\ncnVzdCBTb2x1dGlvbnMsIEluYy4xIzAhBgNVBAMTGkdURSBDeWJlclRydXN0IEds\r\nb2JhbCBSb290MB4XDTA2MDMxNDIwMzAwMFoXDTEzMDMxNDIzNTkwMFowXzELMAkG\r\nA1UEBhMCQkUxEzARBgNVBAoTCkN5YmVydHJ1c3QxFzAVBgNVBAsTDkVkdWNhdGlv\r\nbmFsIENBMSIwIAYDVQQDExlDeWJlcnRydXN0IEVkdWNhdGlvbmFsIENBMIIBIjAN\r\nBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlSKhEB1KRmBuBZGb34PC7RKyWnz4\r\nq+H4UFwoLH5+ADiTsItK8cJMPBAsPO+w7KFpL7n8zAgUa41PGPOD0vqpNwggqlyq\r\ngGCi1aUiAM9a5bSX37oevlyOFxlm/a+ffHuJsg4k2MerY8SVMo1I5mNZfQS4M6i9\r\n111kvGO1900o/fkGcjFcukWUZaPStFjsO2FYRKMvYrObgLSC/dXHzFEl5ZU/Ry8w\r\ne6zIeG7i4W0n6z3MAYLoNXeNq1i7VdHVpIFWjRzQFLGwBt6gkSLz8Kg0F0fG4D72\r\nDFqsflBLzeFpbgb8Bn5qTbSVmaBZXDVm7NlJ1BfgYLBdpdca4ipuZvKvHQIDAQAB\r\no4IBbzCCAWswRQYDVR0fBD4wPDA6oDigNoY0aHR0cDovL3d3dy5wdWJsaWMtdHJ1\r\nc3QuY29tL2NnaS1iaW4vQ1JMLzIwMTgvY2RwLmNybDAdBgNVHQ4EFgQUZWWjPdc7\r\nEaMKByU3yUJKW3Z3UOEwUwYDVR0gBEwwSjBIBgkrBgEEAbE+AQAwOzA5BggrBgEF\r\nBQcCARYtaHR0cDovL3d3dy5wdWJsaWMtdHJ1c3QuY29tL0NQUy9PbW5pUm9vdC5o\r\ndG1sMIGJBgNVHSMEgYEwf6F5pHcwdTELMAkGA1UEBhMCVVMxGDAWBgNVBAoTD0dU\r\nRSBDb3Jwb3JhdGlvbjEnMCUGA1UECxMeR1RFIEN5YmVyVHJ1c3QgU29sdXRpb25z\r\nLCBJbmMuMSMwIQYDVQQDExpHVEUgQ3liZXJUcnVzdCBHbG9iYWwgUm9vdIICAaUw\r\nDgYDVR0PAQH/BAQDAgEGMBIGA1UdEwEB/wQIMAYBAf8CAQAwDQYJKoZIhvcNAQEF\r\nBQADgYEAQ7NFg1RxxB/csjxrTr8m8k7yrZpb+oY3iOgUbEEYQl/vZT7rA3egt551\r\nelF8uxVbuK+RoDSSU+1/KkmErLmAS7XHsiMi++vY+27JPPPS0bu+yRz/bQHbaYAO\r\nmaXqnnuXmI+3zyKcs7hd5akzF3TGlzcPtOkmgl9hCz8ePWTpK5s=\r\n-----END CERTIFICATE-----\r\nCertificate:\r\n    Data:\r\n        Version: 1 (0x0)\r\n        Serial Number: 421 (0x1a5)\r\n        Signature Algorithm: md5WithRSAEncryption\r\n        Issuer: C=US, O=GTE Corporation, OU=GTE CyberTrust Solutions, Inc., CN=GTE CyberTrust Global Root\r\n        Validity\r\n            Not Before: Aug 13 00:29:00 1998 GMT\r\n            Not After : Aug 13 23:59:00 2018 GMT\r\n        Subject: C=US, O=GTE Corporation, OU=GTE CyberTrust Solutions, Inc., CN=GTE CyberTrust Global Root\r\n        Subject Public Key Info:\r\n            Public Key Algorithm: rsaEncryption\r\n            RSA Public Key: (1024 bit)\r\n                Modulus (1024 bit):\r\n                    00:95:0f:a0:b6:f0:50:9c:e8:7a:c7:88:cd:dd:17:\r\n                    0e:2e:b0:94:d0:1b:3d:0e:f6:94:c0:8a:94:c7:06:\r\n                    c8:90:97:c8:b8:64:1a:7a:7e:6c:3c:53:e1:37:28:\r\n                    73:60:7f:b2:97:53:07:9f:53:f9:6d:58:94:d2:af:\r\n                    8d:6d:88:67:80:e6:ed:b2:95:cf:72:31:ca:a5:1c:\r\n                    72:ba:5c:02:e7:64:42:e7:f9:a9:2c:d6:3a:0d:ac:\r\n                    8d:42:aa:24:01:39:e6:9c:3f:01:85:57:0d:58:87:\r\n                    45:f8:d3:85:aa:93:69:26:85:70:48:80:3f:12:15:\r\n                    c7:79:b4:1f:05:2f:3b:62:99\r\n                Exponent: 65537 (0x10001)\r\n    Signature Algorithm: md5WithRSAEncryption\r\n        6d:eb:1b:09:e9:5e:d9:51:db:67:22:61:a4:2a:3c:48:77:e3:\r\n        a0:7c:a6:de:73:a2:14:03:85:3d:fb:ab:0e:30:c5:83:16:33:\r\n        81:13:08:9e:7b:34:4e:df:40:c8:74:d7:b9:7d:dc:f4:76:55:\r\n        7d:9b:63:54:18:e9:f0:ea:f3:5c:b1:d9:8b:42:1e:b9:c0:95:\r\n        4e:ba:fa:d5:e2:7c:f5:68:61:bf:8e:ec:05:97:5f:5b:b0:d7:\r\n        a3:85:34:c4:24:a7:0d:0f:95:93:ef:cb:94:d8:9e:1f:9d:5c:\r\n        85:6d:c7:aa:ae:4f:1f:22:b5:cd:95:ad:ba:a7:cc:f9:ab:0b:\r\n        7a:7f\r\n-----BEGIN CERTIFICATE-----\r\nMIICWjCCAcMCAgGlMA0GCSqGSIb3DQEBBAUAMHUxCzAJBgNVBAYTAlVTMRgwFgYD\r\nVQQKEw9HVEUgQ29ycG9yYXRpb24xJzAlBgNVBAsTHkdURSBDeWJlclRydXN0IFNv\r\nbHV0aW9ucywgSW5jLjEjMCEGA1UEAxMaR1RFIEN5YmVyVHJ1c3QgR2xvYmFsIFJv\r\nb3QwHhcNOTgwODEzMDAyOTAwWhcNMTgwODEzMjM1OTAwWjB1MQswCQYDVQQGEwJV\r\nUzEYMBYGA1UEChMPR1RFIENvcnBvcmF0aW9uMScwJQYDVQQLEx5HVEUgQ3liZXJU\r\ncnVzdCBTb2x1dGlvbnMsIEluYy4xIzAhBgNVBAMTGkdURSBDeWJlclRydXN0IEds\r\nb2JhbCBSb290MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCVD6C28FCc6HrH\r\niM3dFw4usJTQGz0O9pTAipTHBsiQl8i4ZBp6fmw8U+E3KHNgf7KXUwefU/ltWJTS\r\nr41tiGeA5u2ylc9yMcqlHHK6XALnZELn+aks1joNrI1CqiQBOeacPwGFVw1Yh0X4\r\n04Wqk2kmhXBIgD8SFcd5tB8FLztimQIDAQABMA0GCSqGSIb3DQEBBAUAA4GBAG3r\r\nGwnpXtlR22ciYaQqPEh346B8pt5zohQDhT37qw4wxYMWM4ETCJ57NE7fQMh017l9\r\n3PR2VX2bY1QY6fDq81yx2YtCHrnAlU66+tXifPVoYb+O7AWXX1uw16OFNMQkpw0P\r\nlZPvy5TYnh+dXIVtx6quTx8itc2VrbqnzPmrC3p/\r\n-----END CERTIFICATE-----\r\n'}

AddPeer(onelab)

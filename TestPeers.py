#!/usr/bin/env python
###
##############################
###
### preparation / requirements
###
### two separate instances of myplc
### for now they are located on the same box on lurch
###
### expectations :
### your myplcs should more or less come out of the box, 
### I prefer not to alter the default PLC_ROOT_USER value,
### instead we create a PI account on the site_id=1
###
##############################

import xmlrpclib

plc1={ 'name':'plc1 in federation',
       'url':'https://lurch.cs.princeton.edu:443/',
       'builtin_admin_id':'root@localhost.localdomain',
       'builtin_admin_password':'root',
       'peer_admin_name':'plc1@planet-lab.org',
       'peer_admin_password':'peer',
       'nodename':'n11.plc1.org'
       }
plc2={ 'name':'plc2 in federation',
       'url':'https://planetlab-devbox.inria.fr:443/',
       'builtin_admin_id':'root@localhost.localdomain',
       'builtin_admin_password':'root',
       'peer_admin_name':'plc2@planet-lab.org',
       'peer_admin_password':'peer',
       'nodename':'n21.plc2.org'
       }

## we use indexes 1 and 2 
plc=[None,None,None]
# the server objects
s=[None,None,None]
# the authentication objects
a=[None,None,None]
aa=[None,None,None]

def peer_index(i):
    return 3-i

### cant use digits in slice login name
def plain_name (i):
    if i==1:
        return 'one'
    elif i==2:
        return 'two'
    else:
        raise Exception,"Unexpected input in plain_name"

def test00_init (args=[1,2]):
    global plc,s,a,aa
    ## have you loaded this file already (support for reload)
    if plc[1]:
        pass
    else:
        plc=[None,plc1,plc2]
        for i in args:
            url=plc[i]['url']+'/PLCAPI/'
            s[i]=xmlrpclib.Server(url)
            print 'initializing s[%d]'%i,url
            aa[i]={'Username':plc[i]['builtin_admin_id'],
                   'AuthMethod':'password',
                   'AuthString':plc[i]['builtin_admin_password'],
                   'Role':'admin'}
            print 'initialized aa[%d]'%i, aa[i]
            a[i]={'Username':plc[i]['peer_admin_name'],
                  'AuthMethod':'password',
                  'AuthString':plc[i]['peer_admin_password'],
                  'Role':'admin'}
            print 'initialized a[%d]'%i, a[i]

def test00_print (args=[1,2]):
    global plc,s,a,aa
    for i in args:
        print 's[%d]'%i,s[i]
        print 'aa[%d]'%i, aa[i]
        print 'a[%d]'%i, a[i]

def test00_admin (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        person_id=s[i].AddPerson(aa[i],{'first_name':'Local', 'last_name':'PeerPoint', 'role_ids':[10],
                                              'email':plc[i]['peer_admin_name'],'password':plc[i]['peer_admin_password']})
        print '%02d: created peer admin account %d, %s - %s'%(i,person_id,plc[i]['peer_admin_name'],plc[i]['peer_admin_password'])
        plc[i]['peer_admin_id']=person_id

def test00_enable (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        s[i].AdmSetPersonEnabled(aa[i],plc[i]['peer_admin_id'],True)
        s[i].AddRoleToPerson(aa[i],'admin',plc[i]['peer_admin_id'])
        print '%02d: enabled+admin on account %d:%s'%(i,plc[i]['peer_admin_id'],plc[i]['peer_admin_name'])

def test01_check (args=[1,2]):
    global plc,s,a
    for i in args:
        n=len(s[i].GetNodes(aa[i]))
        f=len(s[i].GetForeignNodes(a[i]))
        print '%02d: Checking connection: got %d local nodes & %d foreign nodes'%(i,n,f)

def test01_node (args=[1,2]):
    global plc,s,a
    for i in args:
        n=s[i].AddNode(a[i],1,{'hostname': plc[i]['nodename']})
        print '%02d: Added node %d %s'%(i,n,plc[i]['nodename'])

def test01_peer_person (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        person_id = s[i].AddPerson (a[i], {'first_name':'Peering(plain passwd)', 'last_name':plc[peer]['name'], 'role_ids':[3000],
                                           'email':plc[peer]['peer_admin_name'],'password':plc[peer]['peer_admin_password']})
        print '02%d:Created person %d as the peer person'%(i,person_id)
        plc[i]['peer_person_id']=person_id

def test01_peer (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        peer_id=s[i].AddPeer (a[i], {'peername':plc[peer]['name'],'peer_url':plc[peer]['url'],'person_id':plc[i]['peer_person_id']})
        # NOTE : need to manually reset the encrypted password through SQL at this point
        print '%02d:Created peer %d'%(i,peer_id)
        plc[i]['peer_id']=peer_id
        print "Please MANUALLY set passwd for person_id=%d in DB%d"%(plc[i]['peer_person_id'],i)
    
def test02_refresh (args=[1,2]):
    global plc,s,a
    for i in args:
        print '%02d: Refreshing peer'%(i)
        s[i].RefreshPeer(a[i],plc[i]['peer_id'])

def test03_site (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        ### create a site (required for creating a slice)
        sitename="site"+str(i)
        abbrev_name="abbr"+str(i)
        plain=plain_name(i)
        site_id=s[i].AddSite (a[i], {'name':plc[i]['name'],
                                     'abbreviated_name': abbrev_name,
                                     'login_base': plain,
                                     'is_public': True,
                                     'url': 'http://%s.com/'%abbrev_name,
                                     'max_slices':10})
        ### max_slices does not seem taken into account at that stage
        s[i].UpdateSite(a[i],plc[i]['site_id'],{'max_slices':10})
        print '%02d: Created site %d with max_slices=10'%(i,site_id)
        plc[i]['site_id']=site_id

def test03_slice (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        plain=plain_name(i)
        ### create a slice
        slice_name="slic"+str(i)
        slice_id=s[i].AddSlice (a[i],{'name':'%s_%s'%(plain,slice_name),
                                      'description':'slice %s_%s on plc %s'%(plain,slice_name,plc[i]['name']),
                                      'url':'http://planet-lab.org/%s'%slice_name,
                                      'max_nodes':100,
                                      'instanciation':'plc-instantiated',
                                      })
        print '%02d: created slice %d'%(i,slice_id)
        plc[i]['slice_id']=slice_id
        

def test04_lnode (args=[1,2]):
    global plc,s,a
    for i in args:
        ### add node to it
        hostname=plc[i]['nodename']
        s[i].AddSliceToNodes (a[i], plc[i]['slice_id'],hostname)
        print '%02d: added local node %s'%(i,hostname)

def test04_fnode (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        ### add node to it
        hostname=plc[peer]['nodename']
        s[i].AddSliceToNodes (a[i], plc[i]['slice_id'],hostname)
        print '%02d: added local node %s'%(i,hostname)

def catch_up (args=[1,2]):
    for i in args:
        plc[i]['peer_admin_id']=3
        plc[i]['peer_person_id']=4
        plc[i]['peer_id']=1
        plc[i]['slice_id']=1


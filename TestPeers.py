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
###
### HOWTO
### 
### ----------------------------------------
### # run sql commands - PLC1
### 
### $ chroot /plc1/root psql planetlab4 pgsqluser
###
### # run sql commands - PLC2
### 
### $ chroot /plc2/root psql -h localhost -p 5433 planetlab4 pgsqluser
### but then a password is required
### 9a61ae18-779e-41b6-8a6c-67c439dc73e5
### 
### ----------------------------------------
### # connecting to the API - PLC1
###
### $ chroot /plc1/root
### $ ./Shell.py --config /plc1/root/data/etc/planetlab/plc_config
###
### # connecting to the API - PLC2
###
### $ chroot /plc2/root
### 
### $ ./Shell.py --config /plc2/root/data/etc/planetlab/plc_config -h https://localhost:444/PLCAPI/
### 
### ----------------------------------------
##############################

import xmlrpclib

plc1={ 'name':'plc1 in federation',
       'root':'/plc1/root',
       'url':'https://lurch.cs.princeton.edu:443/',
       'admin_id':'plc1@planet-lab.org',
       'admin_password':'root',
       'dbport':5432,
       'nodename':'n11.plc1.org'
       }
plc2={ 'name':'plc2 in federation',
       'root':'/plc1/root',
       'url':'https://lurch.cs.princeton.edu:444/',
       'admin_id':'plc2@planet-lab.org',
       'admin_password':'root',
       'dbport':5433,
       'nodename':'n21.plc2.org'
       }

plc=[plc1,plc2]
# the server objects
s=[None,None]
# the authentication objects
a=[None,None]

### cant use digits in slice login name
def plain_name (i):
    if i==1:
        return 'one'
    elif i==2:
        return 'two'
    else:
        raise Exception,"Unexpected input in plain_name"

def test00_init (args=[0,1]):
    global plc,s,a
    for i in args:
        url=plc[i]['url']+'/PLCAPI/'
        s[i]=xmlrpclib.Server(url)
        print 'initializing s[%d]'%i,url
        a[i]={'Username':plc[i]['admin_id'],
              'AuthMethod':'password',
              'AuthString':plc[i]['admin_password'],
              'Role':'admin'}
        print 'initialized a[%d]'%i, a[i]

def test00_check (args=[0,1]):
    global plc,s,a
    for i in args:
        n=len(s[i].GetNodes(a[i]))
        f=len(s[i].GetForeignNodes(a[i]))
        print 'Checking connection: got %d local nodes & %d foreign nodes'%(n,f)

def test01_pi (args=[0,1]):
    global plc,s,a
    for i in args:
        peer=1-i
        plc[i]['pi_id']=s[i].AddPerson(a[i],{'first_name':'Local', 'last_name':'PI', 'role_ids':[20],
                                             'email':plc[i]['admin_id'],'password':plc[id]['admin_password']})

def test01_node (args=[0,1]):
    global plc,s,a
    for i in args:
        n=s[i].AddNode(a[i],1,{'hostname': plc[i]['nodename']})
        print '%02d: Added node %d %s',(i+1,n,plc[i]['nodename'])

def test01_peer_person (args=[0,1]):
    global plc,s,a
    for i in args:
        peer=1-i
        person_id = s[i].AddPerson (a[i], {'first_name':'Peering', 'last_name':plc[peer]['name'], 'role_ids':[3000],
                                           'email':plc[peer]['admin_id'],'password':plc[peer]['admin_password']})
        print '02%d:Created person %d as the peer person'%(i+1,person_id)
        plc[i]['peer_person_id']=person_id

def test01_peer (args=[0,1]):
    global plc,s,a
    for i in args:
        peer=1-i
        peer_id=s[i].AddPeer (a[i], {'peername':plc[peer]['name'],'peer_url':plc[peer]['url'],'person_id':plc[i]['peer_person_id']})
        # NOTE : need to manually reset the encrypted password through SQL at this point
        print '%02d:Created peer %d'%(i+1,peer_id)
        plc[i]['peer_id']=peer_id
        print "Please MANUALLY set passwd for person_id=%d in DB%d"%(person_id,i+1)
    
def test02_refresh (args=[0,1]):
    global plc,s,a
    for i in args:
        print '%02d: Refreshing peer'%(i+1)
        s[i].RefreshPeer(plc[i]['peer_id'])
        ###### at this stage both sites know about two nodes, one local and one foreign

def test03_site (args=[0,1]):
    global plc,s,a
    for i in args:
        peer=1-i
        ### create a site (required for creating a slice)
        sitename="site"+str(i+1)
        abbrev_name="abbr"+str(i+1)
        plain=plain_name(i+1)
        site_id=s[i].AddSite (a[i], {'name':plc[i]['name'],
                                     'abbreviated_name': abbrev_name,
                                     'login_base': plain,
                                     'is_public': True,
                                     'url': 'http://%s.com/'%abbrev_name,
                                     'max_slices':10})
        ### max_slices does not seem taken into account at that stage
        s[i].UpdateSite(a[i],plc[i]['site_id'],{'max_slices':10})
        print '%02d: Created site %d with max_slices=10'%(i+1,site_id)
        plc[i]['site_id']=site_id

def test03_slice (args=[0,1]):
    global plc,s,a
    for i in args:
        peer=1-i
        plain=plain_name(i+1)
        ### create a slice
        slice_name="slic"+str(i+1)
        slice_id=s[i].AddSlice (a[i],{'name':'%s_%s'%(plain,slice_name),
                                      'description':'slice %s_%s on plc %s'%(plain,slice_name,plc[i]['name']),
                                      'url':'http://planet-lab.org/%s'%slice_name,
                                      'max_nodes':100,
                                      'instanciation':'plc-instantiated',
                                      })
        print '%02d: created slice %d'%(i+1,slice_id)
        plc[i]['slice_id']=slice_id
        

def test04_lnode (args=[0,1]):
    global plc,s,a
    for i in args:
        ### add node to it
        hostname=plc[i]['nodename']
        s[i].AddSliceToNodes (a[i], plc[i]['slice_id'],hostname)
        print '%02d: added local node %s'%(i+1,hostname)

def test04_fnode (args=[0,1]):
    global plc,s,a
    for i in args:
        peer=1-i
        ### add node to it
        hostname=plc[peer]['nodename']
        s[i].AddSliceToNodes (a[i], plc[i]['slice_id'],hostname)
        print '%02d: added local node %s'%(i+1,hostname)


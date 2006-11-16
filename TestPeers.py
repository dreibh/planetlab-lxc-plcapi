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

# support reloading without wiping everything off
# dunno how to do (defvar plc)

## we use indexes 1 and 2 
try:
    dir(plc)
except:
    plc=[None,None,None]
## the server objects
try:
    dir(s)
except:
    s=[None,None,None]
## the authentication objects
## our user
try:
    dir(a)
except:
    a=[None,None,None]
## the builtin root user for bootstrapping
try:
    dir(aa)
except:
    aa=[None,None,None]

####################
import xmlrpclib
import os

number_nodes=5
number_slices=3
magic_slices = (1,2)

plc1={ 'plcname':'plc1 in federation',
       'hostname':'lurch.cs.princeton.edu',
       'url-format':'https://%s:443/PLCAPI/',
       'builtin_admin_id':'root@localhost.localdomain',
       'builtin_admin_password':'root',
       'peer_admin_name':'plc1@planet-lab.org',
       'peer_admin_password':'peer',
       'node-format':'n1%02d.plc1.org',
       'plainname' : 'one',
       'slice-format' : 's1%02d',
       }
plc2={ 'plcname':'plc2 in federation',
       'hostname':'planetlab-devbox.inria.fr',
       'url-format':'https://%s:443/PLCAPI/',
       'builtin_admin_id':'root@localhost.localdomain',
       'builtin_admin_password':'root',
       'peer_admin_name':'plc2@planet-lab.org',
       'peer_admin_password':'peer',
       'node-format':'n2%02d.plc2.org',
       'plainname' : 'two',
       'slice-format' : 's2%02d',
       }

####################
def peer_index(i):
    return 3-i

def plc_name (i):
    return plc[i]['plcname']

def site_name (i):
    return 'site'+str(i)

def node_name (i,n):
    return plc[i]['node-format']%i

def slice_name (i,n):
    return plc[i]['plainname']+'_'+plc[i]['slice-format']%i

####################
def test00_init (args=[1,2]):
    global plc,s,a,aa
    ## have you loaded this file already (support for reload)
    if plc[1]:
        pass
    else:
        plc=[None,plc1,plc2]
        for i in args:
            url=plc[i]['url-format']%plc[i]['hostname']
            plc[i]['url']=url
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

def check_nodes (en,ef,args=[1,2]):
    global plc,s,a
    for i in args:
        n=len(s[i].GetNodes(a[i]))
        f=len(s[i].GetForeignNodes(a[i]))
        print '%02d: Checking connection: got %d local nodes & %d foreign nodes'%(i,n,f)
        assert n==en
        assert f==ef

# expected : local slices, foreign slices
def check_slices (els,efs,args=[1,2]):
    global plc,s,a
    for i in args:
        ls=len(s[i].GetSlices(a[i]))
        fs=len(s[i].GetForeignSlices(a[i]))
        print '%02d: Checking connection: got %d local slices & %d foreign slices'%(i,ls,fs)
        assert els==ls
        assert efs==fs

def show_nodes (i,node_ids):
    for message,nodes in [ ['LOC',s[i].GetNodes(a[i],node_ids)],
                           ['FOR',s[i].GetForeignNodes(a[i],node_ids)] ]:
        if nodes:
            print '[%s:%d] : '%(message,len(nodes)),
            for node in nodes:
                print node['hostname']+' ',
            print ''

def check_slice_nodes (expected_nodes, is_local_slice, args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        if is_local_slice:
            sname=slice_name(i,i)
            slice=s[i].GetSlices(a[i],[sname])[0]
            message='local'
        else:
            sname=slice_name(peer,peer)
            slice=s[i].GetForeignSlices(a[i],[sname])[0]
            message='foreign'
        print '%02d: %s slice (%s) '%(i,message,sname),
        slice_node_ids=slice['node_ids']
        print 'on nodes ',slice_node_ids
        assert len(slice_node_ids)==expected_nodes
        show_nodes (i,slice_node_ids)

# expected : nodes on local slice
def check_local_slice_nodes (expected, args=[1,2]):
    check_slice_nodes(expected,True,args)

# expected : nodes on foreign slice
def check_foreign_slice_nodes (expected, args=[1,2]):
    check_slice_nodes(expected,False,args)

def check_conf_files (args=[1,2]):
    global plc,s,a
    for i in args:
        nodename=node_name(i,i)
        ndict= s[i].GetSlivers(a[i],[nodename])[0]
        assert ndict['hostname'] == nodename
        conf_files = ndict['conf_files']
        print '%02d: %d conf_files in GetSlivers for node %s'%(i,len(conf_files),nodename)
        for conf_file in conf_files:
            print 'source=',conf_file['source'],'|',
            print 'dest=',conf_file['dest'],'|',
            print 'enabled=',conf_file['enabled'],'|',
            print ''

import pprint
pp = pprint.PrettyPrinter(indent=3)

def check_slivers (esn,args=[1,2]):
    global plc,s,a
    for i in args:
        nodename=node_name(i,i)
        ndict= s[i].GetSlivers(a[i],[nodename])[0]
        assert ndict['hostname'] == nodename
        slivers = ndict['slivers']
        assert len(slivers) == esn
        print '%02d: %d  slivers in GetSlivers for node %s'%(i,len(slivers),nodename)
        for sliver in slivers:
            print '>>slivername = ',sliver['name']
            pp.pprint(sliver)
                

####################
def test00_admin_person (args=[1,2]):
    global plc,s,a
    for i in args:
        email = plc[i]['peer_admin_name']
        try:
            p=s[i].GetPersons(a[i],[email])[0]
            plc[i]['peer_admin_id']=p['person_id']
        except:
            person_id=s[i].AddPerson(aa[i],{'first_name':'Local', 'last_name':'PeerPoint', 'role_ids':[10],
                                            'email':email,'password':plc[i]['peer_admin_password']})
            print '%02d: created peer admin account %d, %s - %s'%(i,person_id,plc[i]['peer_admin_name'],plc[i]['peer_admin_password'])
            plc[i]['peer_admin_id']=person_id

def test00_admin_enable (args=[1,2]):
    global plc,s,a
    for i in args:
        s[i].AdmSetPersonEnabled(aa[i],plc[i]['peer_admin_id'],True)
        s[i].AddRoleToPerson(aa[i],'admin',plc[i]['peer_admin_id'])
        print '%02d: enabled+admin on account %d:%s'%(i,plc[i]['peer_admin_id'],plc[i]['peer_admin_name'])

####################
def test01_site (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        ### create a site (required for creating a slice)
        sitename=site_name(i)
        abbrev_name="abbr"+str(i)
        login_base=plc[i]['plainname']
        try:
            s[i].GetSites(a[i],{'login_base':login_base})[0]
        except:
            site_id=s[i].AddSite (a[i], {'name':plc_name(i),
                                         'abbreviated_name': abbrev_name,
                                         'login_base': login_base,
                                         'is_public': True,
                                         'url': 'http://%s.com/'%abbrev_name,
                                         'max_slices':10})
        ### max_slices does not seem taken into account at that stage
            s[i].UpdateSite(a[i],site_id,{'max_slices':10})
            print '%02d: Created site %d with max_slices=10'%(i,site_id)
            plc[i]['site_id']=site_id

def get_node_id(i,nodename):
    return s[i].GetNodes(a[i],[nodename])[0]['node_id']

def clean_all_nodes (args=[1,2]):
    global plc,s,a
    for i in args:
        print '%02d: Cleaning all nodes'%i
        for node in s[i].GetNodes(a[i]):
            print '%02d: > Cleaning node %d'%(i,node['node_id'])
            s[i].DeleteNode(a[i],node['node_id'])

def test01_node (args=[1,2]):
    global plc,s,a
    for i in args:
        nodename = node_name(i,i)
        try:
            get_node_id(i,nodename)
        except:
            n=s[i].AddNode(a[i],1,{'hostname': nodename})
            print '%02d: Added node %d %s'%(i,n,node_name(i,i))

def test01_delnode (args=[1,2]):
    global plc,s,a
    for i in args:
        nodename = node_name(i,i)
        node_id = get_node_id (i,nodename)
        retcod=s[i].DeleteNode(a[i],nodename)
        print '%02d: Deleted node %d, got %s'%(i,node_id,retcod)

def test01_peer_person (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        email=plc[peer]['peer_admin_name']
        try:
            p=s[i].GetPersons(a[i],[email])[0]
            plc[i]['peer_person_id']=p['person_id']
        except:
            person_id = s[i].AddPerson (a[i], {'first_name':'Peering(plain passwd)', 'last_name':plc_name(peer), 'role_ids':[3000],
                                               'email':email,'password':plc[peer]['peer_admin_password']})
            print '%02d:Created person %d as the peer person'%(i,person_id)
            plc[i]['peer_person_id']=person_id

def test01_peer (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        peername = plc_name(peer)
        try:
            p=s[i].GetPeers (a[i], [peername])[0]
            plc[i]['peer_id']=p['peer_id']
        except:
            peer_id=s[i].AddPeer (a[i], {'peername':peername,'peer_url':plc[peer]['url'],'person_id':plc[i]['peer_person_id']})
            # NOTE : need to manually reset the encrypted password through SQL at this point
            print '%02d:Created peer %d'%(i,peer_id)
            plc[i]['peer_id']=peer_id
            print "PLEASE manually set password for person_id=%d in DB%d"%(plc[i]['peer_person_id'],i)

def test01_peer_passwd (args=[1,2]):
    global plc,s,a
    for i in args:
        # using an ad-hoc local command for now - never could get quotes to reach sql....
        print "Attempting to set passwd for person_id=%d in DB%d"%(plc[i]['peer_person_id'],i),
        retcod=os.system("ssh root@%s new_plc_api/person-password.sh %d"%(plc[i]['hostname'],plc[i]['peer_person_id']))
        print 'got',retcod
    
# this one gets cached 
def get_peer_id (i):
    try:
        return plc[i]['peer_id']
    except:
        peername = plc_name (peer_index(i))
        peer_id = s[i].GetPeers(a[i],[peername])[0]['peer_id']
        plc[i]['peer_id'] = peer_id
        return peer_id

def test02_refresh (args=[1,2]):
    global plc,s,a
    for i in args:
        print '%02d: Refreshing peer'%(i),
        retcod=s[i].RefreshPeer(a[i],get_peer_id(i))
        print ' got ',retcod


def clean_all_slices (args=[1,2]):
    global plc,s,a
    for i in args:
        print '%02d: Cleaning all slices'%i
        for slice in s[i].GetSlices(a[i]):
            slice_id = slice['slice_id']
            if slice_id not in magic_slices:
                print '%02d: > Cleaning slice %d'%(i,slice_id)
                s[i].DeleteSlice(a[i],slice_id)

def get_slice_id (i,name):
    return s[i].GetSlices(a[i],[name])[0]['slice_id']

def test03_slice (args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        plcname=plc_name(i)
        slicename=slice_name(i,i)
        try:
            s[i].GetSlices(a[i],[slicename])[0]
        except:
            slice_id=s[i].AddSlice (a[i],{'name':slicename,
                                          'description':'slice %s on %s'%(slicename,plcname),
                                          'url':'http://planet-lab.org/%s'%slicename,
                                          'max_nodes':100,
                                          'instanciation':'plc-instantiated',
                                          })
            print '%02d: created slice %d'%(i,slice_id)
        

def test04_node_slice (is_local, add_if_true, args=[1,2]):
    global plc,s,a
    for i in args:
        peer=peer_index(i)
        slice_id = get_slice_id (i,slice_name (i,i))
        
        if is_local:
            hostname=node_name(i,i)
            nodetype='local'
        else:
            hostname=node_name(peer,peer)
            nodetype='foreign'
        if add_if_true:
            s[i].AddSliceToNodes (a[i], slice_id,[hostname])
            message="added"
        else:
            s[i].DeleteSliceFromNodes (a[i], slice_id,[hostname])
            message="deleted"
        print '%02d: %s in slice %d %s node %s'%(i,message,slice_id,nodetype,hostname)

def test04_slice_add_lnode (args=[1,2]):
    test04_node_slice (True,True,args)

def test04_slice_add_fnode (args=[1,2]):
    test04_node_slice (False,True,args)

def test04_slice_del_lnode (args=[1,2]):
    test04_node_slice (True,False,args)

def test04_slice_del_fnode (args=[1,2]):
    test04_node_slice (False,False,args)

####################
def test_all_init ():
    test00_init ()
    test00_print ()
    test00_admin_person ()
    test00_admin_enable ()
    test01_peer_person ()
    test01_peer ()
    test01_peer_passwd ()

    test01_site ()

def test_all_nodes ():

    clean_all_nodes ()
    test02_refresh ()
    check_nodes(0,0)
    # create one node on each site
    test01_node ()
    check_nodes (1,0,)
    test02_refresh ()
    check_nodes (1,1,)

    # check deletions
    test01_delnode ([2])
    check_nodes (1,1,[1])
    check_nodes (0,1,[2])
    test02_refresh ()
    check_nodes (1,0,[1])
    check_nodes (0,1,[2])

    # recreate 
    test01_node ([2])
    check_nodes (1,0,[1])
    check_nodes (1,1,[2])
    test02_refresh ()
    check_nodes (1,1,)

    # make sure node indexes differ
    test01_delnode([2])
    test01_node ([2])
    test01_delnode([2])
    test01_node ([2])
    test01_delnode([2])
    test01_node ([2])
    test02_refresh ()
    check_nodes (1,1,)

def test_all_addslices ():

    clean_all_slices ()
    test02_refresh ()

    test03_slice ()
    # each site has 3 local slices and 0 foreign slice
    check_slices (3,0)
    test02_refresh ()
    check_slices (3,1)
    # no slice has any node yet
    check_local_slice_nodes(0)
    check_foreign_slice_nodes(0)

    # insert one local node in local slice on plc1
    test04_slice_add_lnode ([1])
    # of course the change is only local
    check_local_slice_nodes (1,[1])
    check_local_slice_nodes (0,[2])
    check_foreign_slice_nodes(0)

    # refreshing
    test02_refresh ()
    # remember that foreign slices only know about LOCAL nodes
    # so refreshing does not do anything
    check_local_slice_nodes (1,[1])
    check_local_slice_nodes (0,[2])
    check_foreign_slice_nodes(0)

    # now we add a foreign node into local slice
    test04_slice_add_fnode ([1])
    check_local_slice_nodes (2,[1])
    check_foreign_slice_nodes (0,[1])
    check_local_slice_nodes (0,[2])
    check_foreign_slice_nodes (0,[2])

    # refreshing
    test02_refresh ()
    # remember that foreign slices only know about LOCAL nodes
    # so this does not do anything
    check_local_slice_nodes (2,[1])
    check_foreign_slice_nodes (0,[1])
    check_local_slice_nodes (0,[2])
    check_foreign_slice_nodes (1,[2])

    check_slivers(3,[1])
    check_slivers(3,[2])

def test_all_delslices ():
    test04_slice_del_fnode([1])
    check_local_slice_nodes (1,[1])
    check_foreign_slice_nodes (1,[2])
    test02_refresh ()
    check_local_slice_nodes (1,[1])
    check_foreign_slice_nodes (0,[2])
    
    test04_slice_del_lnode([1])
    check_local_slice_nodes (0,[1])
    check_foreign_slice_nodes (0,[2])
    test02_refresh ()
    check_local_slice_nodes (0,[1])
    check_foreign_slice_nodes (0,[2])

def test_all ():
    test_all_init ()
    test_all_nodes ()
    test_all_addslices ()
    test_all_delslices ()

if __name__ == '__main__':
    test_all()
    

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

import getopt
import sys
import time

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

####################
# predefined stuff
# number of 'system' persons
# builtin maint, local root, 2 persons for the peering
system_persons = 4
# among that, 1 gets refreshed - other ones have conflicting names
system_persons_cross = 1

system_slices_ids = (1,2)
def system_slices ():
    return len(system_slices_ids)
def total_slices ():
    return number_slices+system_slices()

# temporary - the myplc I use doesnt know about 'system' yet
def system_slivers ():
#    return len(system_slices_ids)
    return 0
def total_slivers ():
    return number_slices+system_slivers()

####################
# set initial conditions
def define_test (sites,keys,persons,nodes,slices,fast_mode):
    global number_sites, number_keys, number_persons, number_nodes, number_slices, fast_flag
    number_sites = sites
    number_keys=keys
    number_persons=persons
    number_nodes=nodes
    number_slices=slices
    fast_flag=fast_mode

def show_test():
    print '%d sites, %d keys, %d persons, %d nodes & %d slices'%(number_sites, number_keys,number_persons,
								 number_nodes,number_slices)

def fast():
    define_test(1,1,1,1,1,True)
    
def normal():
    define_test (sites=4,keys=2,persons=4,nodes=5,slices=4,fast_mode=False)

def big():
    define_test (sites=16,keys=8,persons=16,nodes=20,slices=16,fast_mode=False)

fast()
#normal()

####################
# argh, for login_name that doesn't accept digits
plain_numbers=['zero','one','two','three','four','five','six','seven','eight','nine','ten',
	       'eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty']
####################
plc1={ 'plcname':'plc1 in federation',
       'hostname':'lurch.cs.princeton.edu',
       'url-format':'https://%s:443/PLCAPI/',
       'builtin-admin-id':'root@plc1.org',
       'builtin-admin-password':'root',
       'peer-admin-name':'peer1@planet-lab.org',
       'peer-admin-password':'peer',
       'node-format':'n1%02d.plc1.org',
       'plainname' : 'one',
       'site-format':'one%s',
       'person-format' : 'user1-%d@plc1.org',
       'key-format':'ssh-rsa 1111111111111111 user%d-key%d',
       'person-password' : 'password1',
       }
plc2={ 'plcname':'plc2 in federation',
       'hostname':'planetlab-devbox.inria.fr',
       'url-format':'https://%s:443/PLCAPI/',
       'builtin-admin-id':'root@plc2.org',
       'builtin-admin-password':'root',
       'peer-admin-name':'peer2@planet-lab.org',
       'peer-admin-password':'peer',
       'node-format':'n2%02d.plc2.org',
       'plainname' : 'two',
       'site-format':'two%s',
       'person-format' : 'user2-%d@plc2.org',
       'key-format':'ssh-rsa 2222222222222222 user%d-key%d',
       'person-password' : 'password2',
       }

####################
def peer_index(i):
    return 3-i

def plc_name (i):
    return plc[i]['plcname']

def site_name (i,n):
    x=site_login_base(i,n)
    return 'Site fullname '+x

def site_login_base (i,n):
    return plc[i]['site-format']%plain_numbers[n]

def person_name (i,n):
    return plc[i]['person-format']%n

def key_name (i,n,k):
    return plc[i]['key-format']%(n,k)

def node_name (i,n):
    return plc[i]['node-format']%n

def map_on_site (n):
    result=(n%number_sites)
    if (result==0):
	result=number_sites
    return result

def slice_name (i,n):
    site_index=map_on_site(n)
    return "%s_slice%d"%(site_login_base(i,site_index),n)

# to have indexes start at 1
def myrange (n):
    return range (1,n+1,1)

def message (*args):
    print "====================",
    print args
    
##########
def timer_start ():
    global epoch
    epoch = time.time()
    print '+++ timer start'

def timer_show ():
    print '+++ %d seconds ellapsed'%(time.time()-epoch)

####################
def test00_init (args=[1,2]):
    timer_start()
    global plc,s,a,aa
    ## have you loaded this file already (support for reload)
    if plc[1]:
        pass
    else:
        plc=[None,plc1,plc2]
        for i in args:
            url=plc[i]['url-format']%plc[i]['hostname']
            plc[i]['url']=url
            s[i]=xmlrpclib.ServerProxy(url,allow_none=True)
            print 'initializing s[%d]'%i,url
            aa[i]={'Username':plc[i]['builtin-admin-id'],
                   'AuthMethod':'password',
                   'AuthString':plc[i]['builtin-admin-password'],
                   'Role':'admin'}
            print 'initialized aa[%d]'%i, aa[i]
            a[i]={'Username':plc[i]['peer-admin-name'],
                  'AuthMethod':'password',
                  'AuthString':plc[i]['peer-admin-password'],
                  'Role':'admin'}
            print 'initialized a[%d]'%i, a[i]

def test00_print (args=[1,2]):
    for i in args:
        print 's[%d]'%i,s[i]
        print 'aa[%d]'%i, aa[i]
        print 'a[%d]'%i, a[i]

def check_nodes (el,ef,args=[1,2]):
    for i in args:
        # use a single request and sort afterwards for efficiency
        # could have used GetNodes's scope as well
        all_nodes = s[i].GetNodes(a[i])
        n = len ([ x for x in all_nodes if x['peer_id'] is None])
        f = len ([ x for x in all_nodes if x['peer_id'] is not None])
        print '%02d: Checking nodes: got %d local (e=%d) & %d foreign (e=%d)'%(i,n,el,f,ef)
        assert n==el
        assert f==ef

def check_keys (el,ef,args=[1,2]):
    for i in args:
        # use a single request and sort afterwards for efficiency
        # could have used GetKeys's scope as well
        all_keys = s[i].GetKeys(a[i])
        n = len ([ x for x in all_keys if x['peer_id'] is None])
        f = len ([ x for x in all_keys if x['peer_id'] is not None])
        print '%02d: Checking keys: got %d local (e=%d) & %d foreign (e=%d)'%(i,n,el,f,ef)
        assert n==el
        assert f==ef

def check_persons (el,ef,args=[1,2]):
    for i in args:
        # use a single request and sort afterwards for efficiency
        # could have used GetPersons's scope as well
        all_persons = s[i].GetPersons(a[i])
        n = len ([ x for x in all_persons if x['peer_id'] is None])
        f = len ([ x for x in all_persons if x['peer_id'] is not None])
        print '%02d: Checking persons: got %d local (e=%d) & %d foreign (e=%d)'%(i,n,el,f,ef)
        assert n==el
        assert f==ef

# expected : local slices, foreign slices
def check_slices (els,efs,args=[1,2]):
    for i in args:
        ls=len(s[i].GetSlices(a[i],{'peer_id':None}))
        fs=len(s[i].GetSlices(a[i],{'~peer_id':None}))
        print '%02d: Checking slices: got %d local (e=%d) & %d foreign (e=%d)'%(i,ls,els,fs,efs)
        assert els==ls
        assert efs==fs

def show_nodes (i,node_ids):
    # same as above
    all_nodes = s[i].GetNodes(a[i],node_ids)
    loc_nodes = filter (lambda n: n['peer_id'] is None, all_nodes)
    for_nodes = filter (lambda n: n['peer_id'] is not None, all_nodes)

    for message,nodes in [ ['LOC',loc_nodes], ['FOR',for_nodes] ] :
        if nodes:
            print '[%s:%d] : '%(message,len(nodes)),
            for node in nodes:
                print node['hostname']+' ',
            print ''

def check_slice_nodes (expected_nodes, is_local_slice, args=[1,2]):
    for ns in myrange(number_slices):
	check_slice_nodes_n (ns,expected_nodes, is_local_slice, args)

def check_slice_nodes_n (ns,expected_nodes, is_local_slice, args=[1,2]):
    for i in args:
        peer=peer_index(i)
        if is_local_slice:
            sname=slice_name(i,ns)
            slice=s[i].GetSlices(a[i],{'name':[sname],'peer_id':None})[0]
            message='local'
        else:
            sname=slice_name(peer,ns)
            slice=s[i].GetSlices(a[i],{'name':[sname],'~peer_id':None})[0]
            message='foreign'
        print '%02d: %s slice %s (e=%d) '%(i,message,sname,expected_nodes),
        slice_node_ids=slice['node_ids']
        print 'on nodes ',slice_node_ids
        show_nodes (i,slice_node_ids)
        assert len(slice_node_ids)>=expected_nodes
	if len(slice_node_ids) != expected_nodes:
	    print 'TEMPORARY'

# expected : nodes on local slice
def check_local_slice_nodes (expected, args=[1,2]):
    check_slice_nodes(expected,True,args)

# expected : nodes on foreign slice
def check_foreign_slice_nodes (expected, args=[1,2]):
    check_slice_nodes(expected,False,args)

def check_conf_files (args=[1,2]):
    for nn in myrange(number_nodes):
	check_conf_files_n (nn,args)

def check_conf_files_n (nn,args=[1,2]):
    for i in args:
        nodename=node_name(i,nn)
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
    for nn in myrange(number_nodes):
	check_slivers_n (nn,esn,args)

# too verbose to check all nodes, let's check only the first one
def check_slivers_1 (esn,args=[1,2]):
    check_slivers_n (1,esn,args)

def check_slivers_n (nn,esn,args=[1,2]):
    for i in args:
        nodename=node_name(i,nn)
        ndict= s[i].GetSlivers(a[i],[nodename])[0]
        assert ndict['hostname'] == nodename
        slivers = ndict['slivers']
        print '%02d: %d slivers (exp. %d) in GetSlivers for node %s'\
              %(i,len(slivers),esn,nodename)
        for sliver in slivers:
            print '>>slivername = ',sliver['name']
            pp.pprint(sliver)
        assert len(slivers) == esn
                

####################
def test00_admin_person (args=[1,2]):
    global plc
    for i in args:
        email = plc[i]['peer-admin-name']
        try:
            p=s[i].GetPersons(a[i],[email])[0]
            plc[i]['peer-admin-id']=p['person_id']
        except:
            person_id=s[i].AddPerson(aa[i],{'first_name':'Local', 
					    'last_name':'PeerPoint', 
					    'role_ids':[10],
                                            'email':email,
					    'password':plc[i]['peer-admin-password']})
            print '%02d:== created peer admin account %d, %s - %s'%(i,
								  person_id,plc[i]['peer-admin-name'],
								  plc[i]['peer-admin-password'])
            plc[i]['peer-admin-id']=person_id

def test00_admin_enable (args=[1,2]):
    for i in args:
        s[i].AdmSetPersonEnabled(aa[i],plc[i]['peer-admin-id'],True)
        s[i].AddRoleToPerson(aa[i],'admin',plc[i]['peer-admin-id'])
        print '%02d:== enabled+admin on account %d:%s'%(i,plc[i]['peer-admin-id'],plc[i]['peer-admin-name'])

def test00_peer_person (args=[1,2]):
    global plc
    for i in args:
        peer=peer_index(i)
        email=plc[peer]['peer-admin-name']
        try:
            p=s[i].GetPersons(a[i],[email])[0]
            plc[i]['peer_person_id']=p['person_id']
        except:
            person_id = s[i].AddPerson (a[i], {'first_name':'Peering(plain passwd)', 'last_name':plc_name(peer), 'role_ids':[3000],
                                               'email':email,'password':plc[peer]['peer-admin-password']})
            print '%02d:Created person %d as the peer person'%(i,person_id)
            plc[i]['peer_person_id']=person_id

####################
def test00_peer (args=[1,2]):
    global plc
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

def test00_peer_passwd (args=[1,2]):
    for i in args:
        # using an ad-hoc local command for now - never could get quotes to reach sql....
        print "Attempting to set passwd for person_id=%d in DB%d"%(plc[i]['peer_person_id'],i),
        retcod=os.system("ssh root@%s new_plc_api/person-password.sh %d"%(plc[i]['hostname'],plc[i]['peer_person_id']))
        print '-> system returns',retcod
    
# this one gets cached 
def get_peer_id (i):
    try:
        return plc[i]['peer_id']
    except:
        peername = plc_name (peer_index(i))
        peer_id = s[i].GetPeers(a[i],[peername])[0]['peer_id']
        plc[i]['peer_id'] = peer_id
        return peer_id

##############################
def test00_refresh (message,args=[1,2]):
    print '=== refresh',message
    timer_show()
    for i in args:
        print '%02d:== Refreshing peer'%(i),
        retcod=s[i].RefreshPeer(a[i],get_peer_id(i))
        print 'got ',retcod
	timer_show()

####################
def test01_site (args=[1,2]):
    for ns in myrange(number_sites):
	test01_site_n (ns,True,args)

def test01_del_site (args=[1,2]):
    for ns in myrange(number_sites):
	test01_site_n (ns,False,args)

def test01_site_n (ns,add_if_true,args=[1,2]):
    for i in args:
	login_base = site_login_base (i,ns)
        try:
	    site_id = s[i].GetSites(a[i],[login_base])[0]['site_id']
	    if not add_if_true:
		s[i].DeleteSite(a[i],site_id)
		print "%02d:== deleted site_id %d"%(i,site_id)
        except:
	    if add_if_true:
		sitename=site_name(i,ns)
		abbrev_name="abbr"+str(i)
		max_slices = number_slices
		site_id=s[i].AddSite (a[i], {'name':plc_name(i),
					     'abbreviated_name': abbrev_name,
					     'login_base': login_base,
					     'is_public': True,
					     'url': 'http://%s.com/'%abbrev_name,
					     'max_slices':max_slices})
                ### max_slices does not seem taken into account at that stage
		s[i].UpdateSite(a[i],site_id,{'max_slices':max_slices})
		print '%02d:== Created site %d with max_slices=%d'%(i,site_id,max_slices)

####################
def test02_person (args=[1,2]):
    for np in myrange(number_persons):
	test02_person_n (np,True,args)

def test02_del_person (args=[1,2]):
    for np in myrange(number_persons):
	test02_person_n (np,False,args)

def test02_person_n (np,add_if_true,args=[1,2]):
    test02_person_n_ks (np, myrange(number_keys),add_if_true,args)

def test02_person_n_ks (np,nks,add_if_true,args=[1,2]):
    for i in args:
        email = person_name(i,np)
        try:
            person_id=s[i].GetPersons(a[i],[email])[0]['person_id']
	    if not add_if_true:
		s[i].DeletePerson(a[i],person_id)
		print "%02d:== deleted person_id %d"%(i,person_id)
        except:
	    if add_if_true:
		password = plc[i]['person-password']
		person_id=s[i].AddPerson(a[i],{'first_name':'Your average', 
					       'last_name':'User%d'%np, 
					       'role_ids':[30],
					       'email':email,
					       'password': password })
		print '%02d:== created user account %d, %s - %s'%(i, person_id,email,password)
		for nk in nks:
		    key=key_name(i,np,nk)
		    s[i].AddPersonKey(aa[i],email,{'key_type':'ssh', 'key':key})
		    print '%02d:== added key %s to person %s'%(i,key,email)

####################
# retrieves node_id from hostname - checks for local nodes only
def get_local_node_id(i,nodename):
    return s[i].GetNodes(a[i],[nodename],None,'local')[0]['node_id']

# clean all local nodes - foreign nodes are not supposed to be cleaned up manually
def clean_all_nodes (args=[1,2]):
    for i in args:
        print '%02d:== Cleaning all nodes'%i
        loc_nodes = s[i].GetNodes(a[i],None,None,'local')
        for node in loc_nodes:
            print '%02d:==== Cleaning node %d'%(i,node['node_id'])
            s[i].DeleteNode(a[i],node['node_id'])

def test03_node (args=[1,2]):
    for nn in myrange(number_nodes):
	test03_node_n (nn,args)

def test03_node_n (nn,args=[1,2]):
    for i in args:
        nodename = node_name(i,nn)
        try:
            get_local_node_id(i,nodename)
        except:
	    login_base=site_login_base(i,map_on_site(nn))
            n=s[i].AddNode(a[i],login_base,{'hostname': nodename})
            print '%02d:== Added node %d %s'%(i,n,node_name(i,i))

def test02_delnode (args=[1,2]):
    for nn in myrange(number_nodes):
	test02_delnode_n (nn,args)

def test02_delnode_n (nn,args=[1,2]):
    for i in args:
        nodename = node_name(i,nn)
        node_id = get_local_node_id (i,nodename)
        retcod=s[i].DeleteNode(a[i],nodename)
        print '%02d:== Deleted node %d, returns %s'%(i,node_id,retcod)

####################
def clean_all_slices (args=[1,2]):
    for i in args:
        print '%02d:== Cleaning all slices'%i
        for slice in s[i].GetSlices(a[i],{'peer_id':None}):
            slice_id = slice['slice_id']
            if slice_id not in system_slices_ids:
                print '%02d:==== Cleaning slice %d'%(i,slice_id)
                s[i].DeleteSlice(a[i],slice_id)

def get_local_slice_id (i,name):
    return s[i].GetSlices(a[i],{'name':[name],'peer_id':None})[0]['slice_id']

def test04_slice (args=[1,2]):
    for n in myrange(number_slices):
	test04_slice_n (n,args)

def test04_slice_n (ns,args=[1,2]):
    for i in args:
        peer=peer_index(i)
        plcname=plc_name(i)
        slicename=slice_name(i,ns)
        max_nodes=number_nodes
        try:
            s[i].GetSlices(a[i],[slicename])[0]
        except:
            slice_id=s[i].AddSlice (a[i],{'name':slicename,
                                          'description':'slice %s on %s'%(slicename,plcname),
                                          'url':'http://planet-lab.org/%s'%slicename,
                                          'max_nodes':max_nodes,
                                          'instanciation':'plc-instantiated',
                                          })
            print '%02d:== created slice %d - max nodes=%d'%(i,slice_id,max_nodes)
	    for np in myrange(number_persons):
		email = person_name (i,np)
		retcod = s[i].AddPersonToSlice (a[i], email, slicename)
		print '%02d:== Attached person %s to slice %s'%(i,email,slicename)
        

def test04_node_slice (is_local, add_if_true, args=[1,2]):
    for ns in myrange(number_slices):
	test04_node_slice_ns (ns,is_local, add_if_true, args)

def test04_node_slice_ns (ns,is_local, add_if_true, args=[1,2]):
    test04_node_slice_nl_n (myrange(number_nodes),ns,is_local, add_if_true, args)

def test04_node_slice_nl_n (nnl,ns,is_local, add_if_true, args=[1,2]):
    for i in args:
        peer=peer_index(i)
        slice_id = get_local_slice_id (i,slice_name (i,ns))
        
        if is_local:
            hostnames=[node_name(i,nn) for nn in nnl]
            nodetype='local'
        else:
            hostnames=[node_name(peer,nn) for nn in nnl]
            nodetype='foreign'
        if add_if_true:
            s[i].AddSliceToNodes (a[i], slice_id,hostnames)
            message="added"
        else:
            s[i].DeleteSliceFromNodes (a[i], slice_id,hostnames)
            message="deleted"
        print '%02d:== %s in slice %d %s '%(i,message,slice_id,nodetype),
        print hostnames

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
    message ("INIT")
    test00_init ()
    test00_print ()
    test00_admin_person ()
    test00_admin_enable ()
    test00_peer_person ()
    test00_peer ()
    test00_peer_passwd ()

def test_all_sites ():
    test01_site ()
    test00_refresh ('after site creation')

def test_all_persons ():
    test02_del_person()
    test00_refresh ('before persons&keys creation')
    check_keys(0,0)
    check_persons(system_persons,system_persons_cross)
    message ("Creating persons&keys")
    test02_person ()
    if not fast_flag:
	message ("1 extra del/add cycle for unique indexes")
	test02_del_person([2])
	test02_person([2])
    check_keys(number_persons*number_keys,0)
    check_persons(system_persons+number_persons,system_persons_cross)
    test00_refresh ('after persons&keys creation')
    check_keys(number_persons*number_keys,number_persons*number_keys)
    check_persons(system_persons+number_persons,system_persons_cross+number_persons)

def test_all_nodes ():

    message ("RESETTING NODES")
    clean_all_nodes ()
    test00_refresh ('cleaned nodes')
    check_nodes(0,0)

    # create one node on each site
    message ("CREATING NODES")
    test03_node ()
    check_nodes(number_nodes,0)
    test00_refresh ('after node creation')
    check_nodes(number_nodes,number_nodes)
    test02_delnode([2])
    if not fast_flag:
	message ("2 extra del/add cycles on plc2 for different indexes")
	test03_node ([2])
	test02_delnode([2])
	test03_node ([2])
	test02_delnode([2])
    check_nodes(0,number_nodes,[2])
    test00_refresh('after deletion on plc2')
    check_nodes(number_nodes,0,[1])
    check_nodes(0,number_nodes,[2])
    message ("ADD on plc2 for different indexes")
    test03_node ([2])
    check_nodes (number_nodes,0,[1])
    check_nodes (number_nodes,number_nodes,[2])
    test00_refresh('after re-creation on plc2')
    check_nodes (number_nodes,number_nodes,)

def test_all_addslices ():

    # reset
    message ("RESETTING SLICES TEST")
    clean_all_nodes ()
    test03_node ()
    clean_all_slices ()
    test00_refresh ("After slices init")

    # create slices on plc1
    message ("CREATING SLICES on plc1")
    test04_slice ([1])
    # each site has 3 local slices and 0 foreign slice
    check_slices (total_slices(),0,[1])
    check_slices (system_slices(),0,[2])
    test00_refresh ("after slice created on plc1")
    check_slices (total_slices(),0,[1])
    check_slices (system_slices(),number_slices,[2])
    # no slice has any node yet
    check_local_slice_nodes(0,[1])
    check_foreign_slice_nodes(0,[2])

    # insert local nodes in local slice on plc1
    message ("ADDING LOCAL NODES IN SLICES")
    test04_slice_add_lnode ([1])
    # of course the change is only local
    check_local_slice_nodes (number_nodes,[1])
    check_foreign_slice_nodes(0,[2])

    # refreshing
    test00_refresh ("After local nodes were added on plc1")
    check_local_slice_nodes (number_nodes,[1])
    check_foreign_slice_nodes (number_nodes,[2])

    # now we add foreign nodes into local slice
    message ("ADDING FOREIGN NODES IN SLICES")
    test04_slice_add_fnode ([1])
    check_local_slice_nodes (2*number_nodes,[1])
    check_foreign_slice_nodes (number_nodes,[2])

    # refreshing
    test00_refresh ("After foreign nodes were added in plc1")
    # remember that foreign slices only know about LOCAL nodes
    # so this does not do anything
    check_local_slice_nodes (2*number_nodes,[1])
    check_foreign_slice_nodes (2*number_nodes,[2])

    check_slivers_1(total_slivers())

def test_all_delslices ():

    message ("DELETING FOREIGN NODES FROM SLICES")
    test04_slice_del_fnode([1])
    check_local_slice_nodes (number_nodes,[1])
    check_foreign_slice_nodes (2*number_nodes,[2])
    # mmh?
    check_slivers_1(total_slivers(),[1])

    test00_refresh ("After foreign nodes were removed on plc1")
    check_local_slice_nodes (number_nodes,[1])
    check_foreign_slice_nodes (number_nodes,[2])
    
    message ("DELETING LOCAL NODES FROM SLICES")
    test04_slice_del_lnode([1])
    check_local_slice_nodes (0,[1])
    check_foreign_slice_nodes (number_nodes,[2])

    test00_refresh ("After local nodes were removed on plc1")
    check_local_slice_nodes (0,[1])
    check_foreign_slice_nodes (0,[2])

    message ("CHECKING SLICES CLEAN UP")
    clean_all_slices([1])
    check_slices (system_slices(),0,[1])
    check_slices (system_slices(),number_slices,[2])
    test00_refresh ("After slices clenaup")
    check_slices(system_slices(),0)

def test_all_slices ():
    test_all_addslices ()
    test_all_delslices ()
    
def test_all ():
    test_all_init ()
    timer_show()
    test_all_sites ()
    timer_show()
    test_all_persons ()
    timer_show()
    test_all_nodes ()
    timer_show()
    test_all_slices ()
    timer_show()
    message("END")

### ad hoc test sequences
def populate ():
    test_all_init()
    test01_site()
    test02_person()
    test03_node()
    test04_slice([1])
    test00_refresh ("populate: refreshing peer 1",[1])
    test04_slice_add_lnode([1])
    test04_slice_add_fnode([1])
    test00_refresh("populate: refresh all")

def test_now ():
    test_all_init()
    test_all_sites ()
#    clean_all_nodes()
#    clean_all_slices()
#    populate()

#####
def usage ():
    print "Usage: %s [-n] [-f]"%sys.argv[0]
    print " -f runs faster (1 node - 1 slice)"
    print " -b performs big run (4 times as large as normal)"
    print " -n runs test_now instead of test_all"
    print " -p runs populate instead of test_all"
    
    sys.exit(1)

def main ():
    try:
        (o,a) = getopt.getopt(sys.argv[1:], "fnpb")
    except:
        usage()
    func = test_all
    for (opt,val) in o:
        if opt=='-f':
            fast()
	elif opt=='-b':
            big()
        elif opt=='-n':
	    print 'Running test_now'
            func = test_now
        elif opt=='-p':
	    print 'Running populate'
            func = populate
        else:
            usage()
    if a:
        usage()
    show_test()
    func()   
 
if __name__ == '__main__':
    normal()
    main()
    

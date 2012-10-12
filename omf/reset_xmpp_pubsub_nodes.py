#!/usr/bin/env /usr/bin/plcsh

import sys
import xmlrpclib
from optparse import OptionParser

sys.path.append("/usr/bin/")
from omf_slicemgr import *
from PLC.Config import Config

config = Config("/etc/planetlab/plc_config")
pubsub=None
verbose=False

def init_global_pubsub(verbose):
    xmppserver = config.PLC_OMF_XMPP_SERVER
    xmppuser = "@".join([config.PLC_OMF_XMPP_USER, xmppserver])
    xmpppass = config.PLC_OMF_XMPP_PASSWORD
    global pubsub
    pubsub = PubSubClient(xmppuser, xmpppass, verbose=verbose)

def init_xmlrpc ():
    return xmlrpclib.ServerProxy(config.PLC_OMF_SLICEMGR_URL)
    

def delete_all_nodes(iq):
    global pubsub
    print "Deleting PubSub groups..."
    for i in iq.query.elements():
        node = i['node']
        if verbose: print 'deleting node',node
        reactor.callLater(1, pubsub.delete_node, node)

def is_local_node(node_id, slice_name):
    try:
        return GetNodes({'node_id': node_id}, ['peer_id'])[0]['peer_id'] == None
    except IndexError:
        print "WARNING: can not find the node with node_id %s" % node_id
        print "WARNING: node_id %s was referenced in slice %s" % (node_id, slice_name)
        return False

def main ():
    usage="Usage: %prog -- [options]"
    parser=OptionParser (usage=usage)
    parser.add_option ("-v","--verbose",action='store_true',dest='verbose',default=False,
                       help="be verbose")
    parser.add_option ("-s","--slice_pattern", action='store', dest='slice_pattern', default=None,
                       help="specify just one slice (or a slice name pattern), for debug mostly")
    (options,args) = parser.parse_args()
    global verbose
    verbose=options.verbose
    if args: 
        parser.print_help()
        sys.exit(1)

    init_global_pubsub (options.verbose)
    xmlrpc = init_xmlrpc ()
    
    pubsub.add_result_hook("discover", delete_all_nodes)
    reactor.callLater(1, pubsub.discover)
    reactor.callLater(2, pubsub.create_node, "/OMF")
    reactor.callLater(2, pubsub.create_node, "/SYSTEM")

    reactor.callLater(4, reactor.stop)
    reactor.connectTCP(pubsub.id.host, 5222, pubsub.factory)
    reactor.run()

    print "Re-creating PubSub groups..."
    if options.slice_pattern:
        slices=GetSlices({'name':options.slice_pattern})
        if not slices:
            print 'Could not find any slice with',options.slice_pattern
            sys.exit(1)
    else:
        slices = GetSlices()
    # optimizing the API calls
    nodes = GetNodes ({},['node_id','hrn','peer_id'])
    local_node_hash = dict ( [ (n['node_id'],n['hrn']) for n in nodes if n['peer_id'] is None ] )
    foreign_node_hash = dict ( [ (n['node_id'],n['hrn']) for n in nodes if n['peer_id'] is not None ] )
    total=len(slices)
    slice_counter=1
    node_counter=0
    for slice in slices:
        print 40*'x' + " slice %s (%d/%d)"%(slice['name'],slice_counter,total)
        slice_counter +=1
        xmlrpc.createSlice(slice['name'])
        for node_id in slice['node_ids']:
            # silently ignore foreign nodes
            if node_id in foreign_node_hash: continue
            elif node_id in local_node_hash:
                hrn=local_node_hash[node_id]
                if hrn:
                    print 'add resource',slice['name'],hrn
                    xmlrpc.addResource(slice['name'],hrn)
                    node_counter +=1
                else:
                    print "WARNING: missing hrn tag for node_id: %s" % node_id
            else:
                print "Cannot find node with node_id %d (in slice %s)"%(node_id,slice['name'])
    print "Re-created a total of %d pubsub nodes"%node_counter

if __name__ == "__main__":
    main()

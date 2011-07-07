#!/usr/bin/env /usr/bin/plcsh

import sys
import xmlrpclib
sys.path.append("/usr/bin/")
from omf_slicemgr import *

xmppserver = config.PLC_OMF_XMPP_SERVER
xmppuser = "@".join([config.PLC_OMF_XMPP_USER, xmppserver])
xmpppass = config.PLC_OMF_XMPP_PASSWORD
xmlrpc = xmlrpclib.ServerProxy(config.PLC_OMF_SLICEMGR_URL)

pubsub = PubSubClient(xmppuser, xmpppass, verbose=False)


def delete_all_nodes(iq):
    global pubsub
    print "Deleting PubSub groups..."
    for i in iq.query.elements():
        node = i['node']
        reactor.callLater(1, pubsub.delete_node, node)

def is_local_node(node_id, slice_name):
    try:
        return GetNodes({'node_id': node_id}, ['peer_id'])[0]['peer_id'] == None
    except IndexError:
        print "WARNING: can not find the node with node_id %s" % node_id
        print "WARNING: node_id %s was referenced in slice %s" % (node_id, slice_name)
        return False

if __name__ == "__main__":
    pubsub.add_result_hook("discover", delete_all_nodes)
    reactor.callLater(1, pubsub.discover)
    reactor.callLater(2, pubsub.create_node, "/OMF")
    reactor.callLater(2, pubsub.create_node, "/SYSTEM")

    reactor.callLater(4, reactor.stop)
    reactor.connectTCP(pubsub.id.host, 5222, pubsub.factory)
    reactor.run()

    print "Re-creating PubSub groups..."
    slices = GetSlices()
    # optimizing the API calls
    nodes = GetNodes ({},['node_id','hrn','peer_id'])
    local_node_hash = dict ( [ (n['node_id'],n['hrn']) for n in nodes if n['peer_id'] is None ] )
    foreign_node_hash = dict ( [ (n['node_id'],n['hrn']) for n in nodes if n['peer_id'] is not None ] )
    total=len(slices)
    counter=1
    for slice in slices:
        print 40*'x' + " slice %s (%d/%d)"%(slice['name'],counter,total)
        counter +=1
        xmlrpc.createSlice(slice['name'])
        for node_id in slice['node_ids']:
            # silently ignore foreign nodes
            if node_id in foreign_node_hash: continue
            elif node_id in local_node_hash:
                hrn=local_node_hash[node_id]
                if hrn:
                    xmlrpc.addResource(slice['name'],hrn)
                else:
                    print "WARNING: missing hrn tag for node_id: %s" % node_id
            else:
                print "Cannot find node with node_id %d (in slice %s)"%(node_id,slice['name'])

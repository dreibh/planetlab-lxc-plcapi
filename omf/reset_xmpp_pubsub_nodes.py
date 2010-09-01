#!/usr/bin/env /usr/bin/plcsh

import sys
import xmlrpclib
sys.path.append("/usr/bin/")
from omf_slicemgr import *

xmlrpc = xmlrpclib.ServerProxy("http://localhost:5053")

xmppserver = config.PLC_OMF_XMPP_SERVER
xmppuser = "@".join([config.PLC_OMF_XMPP_USER, xmppserver])
xmpppass = config.PLC_OMF_XMPP_PASSWORD
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
    for slice in slices:
        xmlrpc.createSlice(slice['name'])
        for node_id in slice['node_ids']:
            try:
                hrn = GetNodeTags({'tagname':'hrn', 'node_id': node_id})[0]['value']
                xmlrpc.addResource(slice['name'], hrn)
            except IndexError:
                if is_local_node(node_id, slice['name']):
                    print "WARNING: missing hrn tag for node_id: %s" % node_id

#!/usr/bin/env /usr/bin/plcsh

import sys
import xmlrpclib
sys.path.append("/usr/bin/")
from omf_slicemgr import *

xmlrpc = xmlrpclib.ServerProxy("http://localhost:5053")

xmppserver = config.PLC_OMF_XMPP_SERVER
xmppuser = "@".join([config.PLC_OMF_XMPP_USER, xmppserver])
xmpppass = config.PLC_OMF_XMPP_PASSWORD
pubsub = PubSubClient(xmppuser, xmpppass, verbose=True)


def delete_all_nodes(iq):
    global pubsub
    print "called"
    for i in iq.query.elements():
        node = i['node']
        reactor.callLater(1, pubsub.delete_node, node)

if __name__ == "__main__":
    pubsub.add_result_hook("discover", delete_all_nodes)
    reactor.callLater(1, pubsub.discover)
    reactor.callLater(2, pubsub.create_node, "/OMF")
    reactor.callLater(2, pubsub.create_node, "/SYSTEM")

    reactor.callLater(4, reactor.stop)
    reactor.connectTCP(pubsub.id.host, 5222, pubsub.factory)
    reactor.run()

    slices = GetSlices()
    for slice in slices:
        xmlrpc.createSlice(slice['name'])
        for node_id in slice['node_ids']:
            node = GetNodes(node_id)[0]['hostname']
            xmlrpc.addResource(slice['name'], node)
            

    

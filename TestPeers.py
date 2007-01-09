#!/usr/bin/python

for peer in GetPeers():
    # Clear out everything
    for node in GetPeerNodes(peer['node_ids']):
        

    print "Refreshing peer", peer['peername']
    print RefreshPeer(peer['peer_id'])

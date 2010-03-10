#!/usr/bin/env python
# Baris Metin <tmetin@sophia.inria.fr>

import os
import sys
import Queue
from twisted.words.xish import domish
from twisted.web import xmlrpc, server
from twisted.internet import reactor, task
from twisted.words.protocols.jabber import xmlstream, client, jid

sys.path.append("/usr/share/plc_api/")
from PLC.Config import Config


class BaseClient(object):
    """ Base XMPP client: handles authentication and basic presence/message requests. """
    def __init__(self, id, secret, verbose = False, log = None):

        if isinstance(id, (str, unicode)):
            id = jid.JID(id)
        x = client.XMPPClientFactory(id, secret)
        x.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.event_connected)
        x.addBootstrap(xmlstream.STREAM_END_EVENT, self.event_disconnected)
        x.addBootstrap(xmlstream.INIT_FAILED_EVENT, self.event_init_failed)
        x.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.event_authenticated)
        self.id = id
        self.factory = x
        self.verbose = verbose
        self.log = log or sys.stdout

    def __rawDataIN(self, buf):
        if self.verbose: self.msg("RECV: %s" % buf)

    def __rawDataOUT(self, buf):
        if self.verbose: self.msg("SEND: %s" % buf)

    def msg(self, msg):
        self.log.write("%s\n" % msg)
        self.log.flush()

    def error(self, msg):
        self.msg("ERROR: %s" % msg)

    def warn(self, msg):
        self.msg("WARN: %s" % msg)

    def info(self, msg):
        self.msg("INFO: %s" % msg)

    def event_connected(self, xs):
        # log all traffic
        xs.rawDataInFn = self.__rawDataIN
        xs.rawDataOutFn = self.__rawDataOUT
        self.xmlstream = xs
        
    def event_disconnected(self, xs):
        pass

    def event_init_failed(self, xs):
        self.error("Init Failed")

    def event_authenticated(self, xs):
        presence = domish.Element(("jabber:client", "presence"))
        presence.addElement("show", content="dnd")
        presence.addElement("status", content="man at work")
        xs.send(presence)

        # add protocol handlers
        xs.addObserver("/presence[@type='subscribe']", self.presence_subscribe)
        xs.addObserver("/presence[@type='unsubscribe']", self.presence_unsubscribe)
        xs.addObserver("/precence", self.presence)
        xs.addObserver("/message[@type='chat']", self.message_chat)

    def presence_subscribe(self, m):
        self.info("%s request to add us, granting." % m['from'])
        p = domish.Element(("jabber:client", "presence"))
        p['from'], p['to'] = m['to'], m['from']
        p['type'] = "subscribed"
        self.xmlstream.send(p)

    def presence_unsubscribe(self, m):
        # try to re-subscribe
        self.info("%s removed us, trying to re-authenticate." % m['from'])
        p = domish.Element(("jabber:client", "presence"))
        p['from'], p['to'] = m['to'], m['from']
        p['type'] = "subscribe"
        self.xmlstream.send(p)

    def presence(self, m):
        p = domish.Element(("jabber:client", "presence"))
        p['from'], p['to'] = m['to'], m['from']
        presence.addElement("show", content="dnd")
        presence.addElement("status", content="man at work")
        self.xmlstream.send(p)

    def message_chat(self, m):
        n = domish.Element((None, "message"))
        n['to'], n['from'] = m['from'], m['to']
        n.addElement("body", content = "don't have time to chat. working!")
        self.xmlstream.send(n)

    
class PubSubClient(BaseClient):
    """ PubSub (XEP 0060) implementation """

    def __init__(self, id, secret, verbose = False, log = None):
        BaseClient.__init__(self, id, secret, verbose = verbose, log = log)
        self.hooks = {}
    
    def add_result_hook(self, hook_to, hook):
        self.hooks[hook_to] = hook

    def delete_result_hook(self, hook_to):
        if self.hooks.has_key(hook_to):
            del self.hooks[hook_to]

    def event_authenticated(self, xs):
        BaseClient.event_authenticated(self, xs)
        self.requests = {}
        xs.addObserver("/iq/pubsub/create", self.result_create_node)
        xs.addObserver("/iq/pubsub/delete", self.result_delete_node)
        xs.addObserver("/iq/query[@xmlns='http://jabber.org/protocol/disco#items']", self.result_discover)

    def __iq(self, t="get"):
        iq = domish.Element((None, "iq"))
        iq['from'] = self.id.full()
        iq['to'] = "pubsub.vplc27.inria.fr"
        iq['type'] = t
        iq.addUniqueId()
        return iq

    def discover(self, node = None):
        iq = self.__iq("get")
        query = iq.addElement("query")
        query['xmlns'] = "http://jabber.org/protocol/disco#items"
        if node:
            query['node'] = node
        self.requests[iq['id']] = node
        self.xmlstream.send(iq)

    def result_discover(self, iq):
        if self.verbose: self.info("Items for node: %s" % self.requests[iq['id']])
        
        hook = self.hooks.get('discover', None)
        for i in iq.query.elements():
            if self.verbose: self.msg(i.toXml())
            if hook: hook(i)
        self.requests.pop(iq['id'])

    def create_node(self, node = None):
        iq = self.__iq("set")
        pubsub = iq.addElement("pubsub")
        pubsub['xmlns'] = "http://jabber.org/protocol/pubsub"
        create = pubsub.addElement("create")
        if node:
            create['node'] = node
        configure = pubsub.addElement("configure")
        self.requests[iq['id']] = node
        self.xmlstream.send(iq)

    def result_create_node(self, iq):
#         if hasattr(iq, "error"):
#             node = self.requests[iq['id']]
#             if hasattr(iq.error, "conflict"):
#                 # node is already there, nothing important.
#                 self.warn("NodeID exists: %s" % node)
#             else:
#                 err_type = ""
#                 err_name = ""
#                 if iq.error:
#                     if iq.error.has_key('type'):
#                         err_type = iq.error['type']
#                     if iq.error.firstChildElement and hasattr(iq.error.firstChildElement, "name"):
#                         err_name = iq.error.firstChildElement.name
#                 self.error("Can not create node: %s (error type: %s, %s)" %  (node, err_type, err_name))
        self.requests.pop(iq['id'])


    def delete_node(self, node):
        iq = self.__iq("set")
        pubsub = iq.addElement("pubsub")
        pubsub['xmlns'] = "http://jabber.org/protocol/pubsub#owner"
        delete = pubsub.addElement("delete")
        delete['node'] = node
        self.requests[iq['id']] = node
        self.xmlstream.send(iq)

    def result_delete_node(self, iq):
        self.requests.pop(iq['id'])




class Slicemgr(xmlrpc.XMLRPC, PubSubClient):
    
    DOMAIN = "/OMF"
    RESOURCES = 'resources'

    def __init__(self, id, secret, verbose = False, log = None):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        PubSubClient.__init__(self, id, secret, verbose = verbose, log = log)
        self.command_queue = Queue.Queue()

        xmlrpc.addIntrospection(self)

    def xmlrpc_createSlice(self, slice):
        self.create_slice(slice)

    def xmlrpc_addResource(self, slice, resource):
        self.add_resource(slice, resource)

    def xmlrpc_deleteSlice(self, slice):
        self.delete_slice(slice)

    def xmlrpc_removeResource(self, slice, resource):
        self.delete_resource(slice, resource)


    def flush_commands(self):
#        self.info("Running %d commands" % self.command_queue.qsize())
        while not self.command_queue.empty():
            (meth, param) = self.command_queue.get()
            meth(param)

    def create_slice(self, slice):
        self.command_queue.put(( self.create_node, "/".join([self.DOMAIN,slice]) ))
        self.command_queue.put(( self.create_node, "/".join([self.DOMAIN,slice,self.RESOURCES]) ))

    def add_resource(self, slice, resource):
        self.command_queue.put(( self.create_node, "/".join([self.DOMAIN,slice,self.RESOURCES,resource]) ))

    def delete_slice(self, slice):
        slice_prefix = "/".join([self.DOMAIN,slice])
        resource_prefix = "/".join([self.DOMAIN,slice,self.RESOURCES])
        def delete_slice_resources(iq):
            node = iq['node']
            if node.startswith(resource_prefix):
                self.command_que.put(self.delete_node, node)

        self.add_result_hook("discover", delete_slice_resources)
        self.discover()
        self.delete_result_hook("discover")

        self.command_queue.put(( self.delete_node, resource_prefix) )
        self.command_queue.put(( self.delete_node, slice_prefix) )

    def delete_resource(self, slice, resource):
        self.command_queue.put(( self.delete_node, "/".join([self.DOMAIN,slice,self.RESOURCES,resource]) ))
        


if __name__ == "__main__":

    config = Config("/etc/planetlab/plc_config")

    xmppserver = config.PLC_OMF_XMPP_SERVER
    xmppuser = "@".join([config.PLC_OMF_XMPP_USER, xmppserver])
    xmpppass = config.PLC_OMF_XMPP_PASSWORD
    slicemgr = Slicemgr(xmppuser, xmpppass,
                        log=open("/var/log/omf/pubsub_client.log", "a"),
                        verbose=True)

    t = task.LoopingCall(slicemgr.flush_commands)
    t.start(5.0) # check every 5 seconds
    reactor.connectTCP(slicemgr.id.host, 5222, slicemgr.factory)
    reactor.listenTCP(5053, server.Site(slicemgr), interface="localhost")
    reactor.run(installSignalHandlers=True)




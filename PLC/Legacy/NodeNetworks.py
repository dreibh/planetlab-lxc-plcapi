# Thierry Parmentelat - INRIA
# $Id$

from PLC.Method import Method
import v42legacy
import sys
current_module=sys.modules[__name__]

methods = [
    "AddNodeNetwork",
    "AddNodeNetworkSetting",
    "DeleteNodeNetwork",
    "DeleteNodeNetworkSetting",
    "GetNodeNetworkSettings",
    "GetNodeNetworks",
    "UpdateNodeNetwork",
    "UpdateNodeNetworkSetting",
]

# argument mapping
v42_to_v43_argmap = {
    "nodenetwork_id":"interface_id",
    "nodenetwork_ids":"interface_ids",
    "nodenetworksetting_ids":"interface_tag_ids",
    }
v43_to_v42_argmap = dict([ (v,k) for k,v in v42_to_v43_argmap.iteritems()])
def v42rename (x): return v42_to_v43_argmap.get(x,x)
def v43rename (x): return v43_to_v42_argmap.get(x,x)

# attach methods here
for legacyname in methods:
    # new method name
    newname=legacyname.replace("NodeNetwork","Interface").replace("Setting","Tag")
    path = "PLC.Methods."
    setattr(current_module,legacyname,v42legacy.make_class(legacyname,newname,path,v42rename,v43rename))

# GetNodes update
# first replace the call method so we can translate fields
c = getattr(v42legacy.import_deep("PLC.Methods.GetNodes"),"GetNodes")
# rename call to newcall so we can still invoke
original = getattr(c,"call")
setattr(c,"newcall",original)

# 4.2 legacy support; update node_fields to include nodenetwork_ids
from PLC.Parameter import Parameter, Mixed, python_type
from PLC.Filter import Filter
from PLC.Nodes import Node, Nodes

node_fields = {}
node_fields['nodenetwork_ids']=Parameter([int], "Legacy version of interface_ids")
for k,v in Node.fields.iteritems():
    node_fields[k]=v

if False:
    expected = node_fields['nodenetwork_ids']
    print "type of nodenetwork_ids = %s" % python_type(node_fields['nodenetwork_ids'])
    print Filter(node_fields).fields.keys()
    print Filter(Node.fields).fields.keys()

accepts = getattr(c,"accepts")
arg0=accepts[0]
arg1=Mixed([Mixed(Node.fields['node_id'],
                  Node.fields['hostname'])],
           Parameter(str,"hostname"),
           Parameter(int,"node_id"),
           Filter(node_fields))
arg2=accepts[2]
newaccepts = [arg0,arg1,arg2]
setattr(c,"accepts",newaccepts)
newreturns = [node_fields]
setattr(c,"returns",newreturns)

def GetNodesCall(self, auth, node_filter = None, return_fields = None):
    global original
    # convert nodenetwork_ids -> interface_ids
    if node_filter <> None and \
           node_filter.has_key('nodenetwork_ids') and \
           not node_filter.has_key('interface_ids'):
        node_filter['interface_ids']=node_filter['nodenetwork_ids']
        
    nodes = original(self,auth,node_filter,return_fields)

    # add in a interface_ids -> nodenetwork_ids
    for node in nodes:
        if node.has_key('interface_ids'):
            node['nodenetwork_ids']=node['interface_ids']

    return nodes

setattr(c,"call",GetNodesCall)

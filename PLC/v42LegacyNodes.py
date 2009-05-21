# $Id: $

from PLC.Parameter import Parameter, Mixed, python_type
from PLC.Filter import Filter
from PLC.Nodes import Node, Nodes

def import_deep(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

# GetNodes update
c = getattr(import_deep("PLC.Methods.GetNodes"),"GetNodes")
# rename call to __origcall so we can still invoke
original = getattr(c,"call")
setattr(c,"__origcall",original)

node_fields = {}
node_fields['nodenetwork_ids']=Parameter([int], "Legacy version of interface_ids")
for k,v in Node.fields.iteritems():
    node_fields[k]=v

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
    # convert nodenetwork_ids -> interface_ids
    if node_filter <> None and \
           node_filter.has_key('nodenetwork_ids') and \
           not node_filter.has_key('interface_ids'):
        node_filter['interface_ids']=node_filter['nodenetwork_ids']
        
    nodes = self.__origcall(auth,node_filter,return_fields)

    # add in a interface_ids -> nodenetwork_ids
    for node in nodes:
        if node.has_key('interface_ids'):
            node['nodenetwork_ids']=node['interface_ids']

    return nodes

setattr(c,"call",GetNodesCall)

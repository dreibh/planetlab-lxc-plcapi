# $Id: $

# mapping of argument/return names for *NodeNetwork* and *Interface* calls
v42_to_v43_argmap = {
    "nodenetwork_id":"interface_id",
    "nodenetwork_ids":"interface_ids",
    "nodenetwork_setting_ids":"interface_tag_ids",
}
v43_to_v42_argmap = dict([ (v,k) for k,v in v42_to_v43_argmap.iteritems()])

def v42rename (x): return v42_to_v43_argmap.get(x,x)
def v43rename (x): return v43_to_v42_argmap.get(x,x)

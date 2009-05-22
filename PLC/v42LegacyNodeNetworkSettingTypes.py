# $Id: $

# mapping of argument/return names for *NodeNetworkSettingType*
v42_to_v43_argmap = { "name":"tagname",
                      "nodenetwork_setting_type_id": "tag_type_id",
                      }
v43_to_v42_argmap = dict([ (v,k) for k,v in v42_to_v43_argmap.iteritems()])

def v42rename (x): return v42_to_v43_argmap.get(x,x)
def v43rename (x): return v43_to_v42_argmap.get(x,x)

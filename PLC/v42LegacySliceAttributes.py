# $Id$
# $URL$

# mapping of argument/return names for *{SliceAttribute,NetworkSetting}Type* and *TagType* calls

v42_to_v43_argmap = { "name":"tagname",
                      "slice_attribute_id":"slice_tag_id",
                      }
v43_to_v42_argmap = dict([ (v,k) for k,v in v42_to_v43_argmap.iteritems()])

def v42rename (x): return v42_to_v43_argmap.get(x,x)
def v43rename (x): return v43_to_v42_argmap.get(x,x)

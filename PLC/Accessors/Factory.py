# Thierry Parmentelat - INRIA
# $Id$

from types import NoneType

from PLC.Method import Method
from PLC.Auth import Auth
from PLC.Parameter import Parameter, Mixed

from PLC.Faults import *

from PLC.Nodes import Node
from PLC.Interfaces import Interface
from PLC.Slices import Slice
from PLC.Ilinks import Ilink

from PLC.TagTypes import TagTypes, TagType

# known classes : { class -> secondary_key }
taggable_classes = { Node : 'hostname', 
                     Interface : None, 
                     Slice: 'login_base', 
                     Ilink : None}

# xxx probably defined someplace else
all_roles = [ 'admin', 'pi', 'tech', 'user', 'node' ]

# generates 2 method classes:
# Get<classname><methodsuffix> (auth, id_or_name) -> tagvalue or None
# Set<classname><methodsuffix> (auth, id_or_name, tagvalue) -> None
# tagvalue is always a string, no cast nor typecheck for now
#
# note: tag_min_role_id gets attached to the tagtype instance, 
# while get_roles and set_roles get attached to the created methods
# 
# returns a tuple (get_method, set_method)
# See Accessors* for examples

def get_set_factory (objclass, methodsuffix, 
                     tagname, category, description, tag_min_role_id=10,
                     get_roles=['admin'], set_roles=['admin']):
    
    if objclass not in taggable_classes:
        try:
            raise PLCInvalidArgument,"PLC.Accessors.Factory: unknown class %s"%objclass.__name__
        except:
            raise PLCInvalidArgument,"PLC.Accessors.Factory: unknown class ??"
    classname=objclass.__name__
    get_name = "Get" + classname + methodsuffix
    set_name = "Set" + classname + methodsuffix

    # create method objects under PLC.Method.Method
    get_class = type (get_name, (Method,),
                      {"__doc__":"Accessor 'get' method designed for %s objects using tag %s"%\
                           (classname,tagname)})
    set_class = type (set_name, (Method,),
                      {"__doc__":"Accessor 'set' method designed for %s objects using tag %s"%\
                           (classname,tagname)})
    # accepts 
    get_accepts = [ Auth () ]
    primary_key=objclass.primary_key
    secondary_key = taggable_classes[objclass]
    if not secondary_key:
        get_accepts += [ objclass.fields[primary_key] ]
    else:
        get_accepts += [ Mixed (objclass.fields[primary_key], objclass.fields[secondary_key]) ]
    # for set, idem + one additional arg
    set_accepts = get_accepts + [ Parameter (str,"New tag value") ]

    # returns
    get_returns = Mixed (Parameter (str), Parameter(NoneType))
    set_returns = Parameter(NoneType)

    # store in classes
    setattr(get_class,'roles',get_roles)
    setattr(get_class,'accepts',get_accepts)
    setattr(get_class,'returns', get_returns)
    setattr(get_class,'skip_typecheck',True)

    setattr(set_class,'roles',set_roles)
    setattr(set_class,'accepts',set_accepts)
    setattr(set_class,'returns', set_returns)
    setattr(set_class,'skip_typecheck',True)

    # body of the get method
    def get_call (self, auth, id_or_name):
        print 'Automagical Accessor get method',classname,get_name,tagname,primary_key,secondary_key
        print 'Warning: PLC/Accessors/Factory is an ongoing work'
        tag_type_id = locate_or_create_tag_type_id (self.api, tagname, 
                                                    category, description, tag_min_role_id)
        return 'foobar'
    setattr (get_class,"call",get_call)

    # body of the set method
    def set_call (self, auth, id_or_name, tagvalue):
        print 'Automagical Accessor set method',classname,get_name,tagname,primary_key,secondary_key
        print 'Warning: PLC/Accessors/Factory is an ongoing work'
        return None
    setattr (set_class,"call",set_call)

    return ( get_class, set_class )

### might need to use a cache
def locate_or_create_tag_type_id (api, tagname, category, description, min_role_id):
    # search tag
    tag_types = TagTypes (api, {'tagname':tagname})
    # not found: create it
    if tag_types:
        print 'FOUND preexisting'
        tag_type_id = tag_types[0]['tag_type_id']
    else:
        print 'not FOUND : creating'
        tag_type_fields = {'tagname':tagname, 
                           'category' :  category,
                           'description' : description,
                           'min_role_id': min_role_id}
        tag_type = TagType (api, tag_type_fields)
        tag_type.sync()
        tag_type_id = tag_type['tag_type_id']

    return tag_type_id

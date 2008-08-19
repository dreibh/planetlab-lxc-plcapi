# Thierry Parmentelat - INRIA
# $Id$

from types import NoneType

from PLC.Method import Method
from PLC.Auth import Auth
from PLC.Parameter import Parameter, Mixed

from PLC.Faults import *

from PLC.Nodes import Nodes, Node
from PLC.NodeTags import NodeTags, NodeTag
from PLC.Interfaces import Interfaces, Interface
from PLC.InterfaceSettings import InterfaceSettings, InterfaceSetting
from PLC.Slices import Slices, Slice
from PLC.SliceAttributes import SliceAttributes, SliceAttribute

# this is another story..
#from PLC.Ilinks import Ilink

from PLC.TagTypes import TagTypes, TagType

# known classes : { class -> secondary_key }
taggable_classes = { Node : {'table_class' : Nodes, 
                             'joins_class' : NodeTags, 'join_class' : NodeTag,
                             'value_key': 'tagvalue', 'secondary_key': 'hostname'},
                     Interface : {'table_class' : Interfaces, 
                                  'joins_class': InterfaceSettings, 'join_class': InterfaceSetting,
                                  'value_key' : 'value' }, 
                     Slice: {'table_class' : Slices, 
                             'joins_class': SliceAttributes, 'join_class': SliceAttribute,
                             'value_key' : 'value', 'secondary_key':'login_base'},
#                     Ilink : xxx
                     }

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

def define_accessors (module, objclass, methodsuffix, 
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
    try:
        secondary_key = taggable_classes[objclass]['secondary_key']
        get_accepts += [ Mixed (objclass.fields[primary_key], objclass.fields[secondary_key]) ]
    except:
        secondary_key = None
        get_accepts += [ objclass.fields[primary_key] ]
    # for set, idem set of arguments + one additional arg, the new value
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
    
    table_class = taggable_classes[objclass]['table_class']
    joins_class = taggable_classes[objclass]['joins_class']
    join_class = taggable_classes[objclass]['join_class']
    value_key = taggable_classes[objclass]['value_key']

    # body of the get method
    def get_call (self, auth, id_or_name):
        # search the tagtype - xxx - might need a cache
        tag_types = TagTypes (self.api, {'tagname': tagname})
        if not tag_types:
            return None
        tag_type_id = tag_types[0]['tag_type_id']
        filter = {'tag_type_id':tag_type_id}
        if isinstance (id_or_name,int):
            filter[primary_key]=id_or_name
        else:
            filter[secondary_key]=id_or_name
        joins = joins_class (self.api,filter,[value_key])
        if not joins:
            # xxx - we return None even if id_or_name is not valid 
            return None
        else:
            return joins[0][value_key]

    # attach it
    setattr (get_class,"call",get_call)

    # body of the set method 
    def set_call (self, auth, id_or_name, tagvalue):
        # locate the object
        if isinstance (id_or_name, int):
            filter={primary_key:id_or_name}
        else:
            filter={secondary_key:id_or_name}
        objs = table_class(self.api, filter,[primary_key])
        if not objs:
            raise PLCInvalidArgument, "Cannot set tag on %s %r"%(objclass.__name__,id_or_name)
        primary_id = objs[0][primary_key]
                           
        # search tag type & create if needed
        tag_types = TagTypes (self.api, {'tagname':tagname})
        if tag_types:
            tag_type = tag_types[0]
        else:
            # not found: create it
            tag_type_fields = {'tagname':tagname, 
                               'category' :  category,
                               'description' : description,
                               'min_role_id': tag_min_role_id}
            tag_type = TagType (self.api, tag_type_fields)
            tag_type.sync()
        tag_type_id = tag_type['tag_type_id']

        # locate the join object (e.g. NodeTag, SliceAttribute or InterfaceSetting)
        filter = {'tag_type_id':tag_type_id}
        if isinstance (id_or_name,int):
            filter[primary_key]=id_or_name
        else:
            filter[secondary_key]=id_or_name
        joins = joins_class (self.api,filter)
        # setting to something non void
        if tagvalue is not None:
            if not joins:
                join = join_class (self.api)
                join['tag_type_id']=tag_type_id
                join[primary_key]=primary_id
                join[value_key]=tagvalue
                join.sync()
            else:
                joins[0][value_key]=tagvalue
                joins[0].sync()
        # providing an empty value means clean up
        else:
            if joins:
                join=joins[0]
                join.delete()

    # attach it
    setattr (set_class,"call",set_call)

    # define in module
    setattr(module,get_name,get_class)
    setattr(module,set_name,set_class)
    # add in <module>.methods
    try:
        methods=getattr(module,'methods')
    except:
        methods=[]
    methods += [get_name,set_name]
    setattr(module,'methods',methods)

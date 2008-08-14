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

# known classes : { class -> secondary_key }
taggable_classes = { Node : 'hostname', Interface : None, Slice: 'login_base', Ilink : None}

# generates 2 method classes:
# Get<classname><methodsuffix> (auth, id_or_name) -> tagvalue or None
# Set<classname><methodsuffix> (auth, id_or_name, tagvalue) -> None
# tagvalue is always a string, no cast nor typecheck for now
#
# note: tag_min_role_id gets attached to the tagtype instance, 
# while get_roles and set_roles get attached to the created methods
# 
# returns a tuple (get_method, set_method)
# See Shortcuts.py for examples

def get_set_factory (objclass, methodsuffix, 
                     tagname, category, description, tag_min_role_id=10,
                     get_roles=['admin'], set_roles=['admin']):
    
    if objclass not in taggable_classes:
        try:
            raise PLCInvalidArgument,"PLC.Shortcuts.Factory: unknown class %s"%objclass.__name__
        except:
            raise PLCInvalidArgument,"PLC.Shortcuts.Factory: unknown class ??"
    classname=objclass.__name__
    get_name = "Get" + classname + methodsuffix
    set_name = "Set" + classname + methodsuffix

    # create method objects under PLC.Method.Method
    get_class = type (get_name, (Method,),
                      {"__doc__":"Shortcut 'get' method designed for %s objects using tag %s"%\
                           (classname,tagname)})
    set_class = type (set_name, (Method,),
                      {"__doc__":"Shortcut 'set' method designed for %s objects using tag %s"%\
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
        print 'Automagical Shortcut get method',classname,get_name,tagname,primary_key,secondary_key
        print 'Warning: PLC/Shortcuts/Factory is an ongoing work'
        return 'foobar'
    setattr (get_class,"call",get_call)

    # body of the set method
    def set_call (self, auth, id_or_name, tagvalue):
        print 'Automagical Shortcut set method',classname,get_name,tagname,primary_key,secondary_key
        print 'Warning: PLC/Shortcuts/Factory is an ongoing work'
        return None
    setattr (set_class,"call",set_call)

    return ( get_class, set_class )


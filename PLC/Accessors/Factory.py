#
# Thierry Parmentelat - INRIA
#
from types import NoneType

from PLC.Faults import *

from PLC.Auth import Auth
from PLC.Parameter import Parameter, Mixed
from PLC.Method import Method
from PLC.Accessor import Accessor, AccessorSingleton

from PLC.Nodes import Nodes, Node
from PLC.NodeTags import NodeTags, NodeTag
from PLC.Interfaces import Interfaces, Interface
from PLC.InterfaceTags import InterfaceTags, InterfaceTag
from PLC.Slices import Slices, Slice
from PLC.SliceTags import SliceTags, SliceTag
from PLC.Sites import Sites, Site
from PLC.SiteTags import SiteTags, SiteTag
from PLC.Persons import Persons, Person
from PLC.PersonTags import PersonTags, PersonTag

# need to import so the core classes get decorated with caller_may_write_tag
from PLC.AuthorizeHelpers import AuthorizeHelpers

# known classes : { class -> details }
taggable_classes = { Node : {'table_class' : Nodes,
                             'joins_class' : NodeTags, 'join_class' : NodeTag,
                             'secondary_key': 'hostname'},
                     Interface : {'table_class' : Interfaces,
                                  'joins_class': InterfaceTags, 'join_class': InterfaceTag,
                                  'secondary_key' : 'ip'},
                     Slice: {'table_class' : Slices,
                             'joins_class': SliceTags, 'join_class': SliceTag,
                             'secondary_key':'name'},
                     Site: {'table_class' : Sites,
                             'joins_class': SiteTags, 'join_class': SiteTag,
                             'secondary_key':'login_base'},
                     Person: {'table_class' : Persons,
                             'joins_class': PersonTags, 'join_class': PersonTag,
                             'secondary_key':'email'},
                     }

# xxx probably defined someplace else
admin_roles = ['admin']
person_roles = [ 'admin', 'pi', 'tech', 'user' ]
all_roles = [ 'admin', 'pi', 'tech', 'user', 'node' ]
tech_roles = [ 'admin', 'pi', 'tech' ]

#
# generates 2 method classes:
# Get<classname><methodsuffix> (auth, id_or_name) -> value or None
# Set<classname><methodsuffix> (auth, id_or_name, value) -> value
# value is always a string, no cast nor typecheck for now
#
# The expose_in_api flag tells whether this tag may be handled
#   through the Add/Get/Update methods as a native field
#
# note: set_roles get attached as 'roles' to the tagtype instance,
# also get_roles and set_roles get attached to the created methods
#
# in addition a convenience method like e.g. LocateNodeArch is defined
# in the Accessor class; its purpose is to retrieve the tag, or to create it if needed
# 
# Legacy NOTE:
# prior to plcapi-5.0-19, this used to accept an additional argument
# named min_role_id; this was redundant and confusing, it has been
# removed, we now use set_roles to restrict write access on the corresponding tag

# the convention here is that methodsuffix should be mixed case, e.g. MyStuff
# while tagname is expected to be lowercase
# you then end up with e.g. GetPersonMyStuff

# the entry point accepts a single class or a list of classes
def define_accessors (module, objclasses, *args, **kwds):
    if not isinstance(objclasses,list):
        objclasses=[objclasses]
    for objclass in objclasses:
        define_accessors_ (module, objclass, *args, **kwds)

# this is for one class
def define_accessors_ (module, objclass, methodsuffix, tagname,
                       category, description,
                       get_roles=all_roles, set_roles=admin_roles, 
                       expose_in_api = False):

    if objclass not in taggable_classes:
        try:
            raise PLCInvalidArgument,"PLC.Accessors.Factory: unknown class %s"%objclass.__name__
        except:
            raise PLCInvalidArgument,"PLC.Accessors.Factory: unknown class ??"

    # side-effect on, say, Node.tags, if required
    if expose_in_api:
        getattr(objclass,'tags')[tagname]=Parameter(str,"accessor")

    classname=objclass.__name__
    get_name = "Get" + classname + methodsuffix
    set_name = "Set" + classname + methodsuffix
    locator_name = "Locate" + classname + methodsuffix

    # accessor method objects under PLC.Method.Method
    get_class = type (get_name, (Method,),
                      {"__doc__":"Accessor 'get' method designed for %s objects using tag %s"%\
                           (classname,tagname)})
    set_class = type (set_name, (Method,),
                      {"__doc__":"Accessor 'set' method designed for %s objects using tag %s"%\
                           (classname,tagname)})

    # accepts
    get_accepts = [ Auth () ]
    primary_key=objclass.primary_key
    secondary_key = taggable_classes[objclass]['secondary_key']
    get_accepts += [ Mixed (objclass.fields[primary_key], objclass.fields[secondary_key]) ]
    # for set, idem set of arguments + one additional arg, the new value
    set_accepts = get_accepts + [ Parameter (str,"New tag value") ]

    # returns
    get_returns = Mixed (Parameter (str), Parameter(NoneType))
    set_returns = Parameter(NoneType)

    # store in classes
    setattr(get_class,'roles',get_roles)
    setattr(get_class,'accepts',get_accepts)
    setattr(get_class,'returns', get_returns)
# that was useful for legacy method only, but we now need type_checking
#    setattr(get_class,'skip_type_check',True)

    setattr(set_class,'roles',set_roles)
    setattr(set_class,'accepts',set_accepts)
    setattr(set_class,'returns', set_returns)
# that was useful for legacy method only, but we now need type_checking
#    setattr(set_class,'skip_type_check',True)

    table_class = taggable_classes[objclass]['table_class']
    joins_class = taggable_classes[objclass]['joins_class']
    join_class = taggable_classes[objclass]['join_class']

    # locate the tag and create it if needed
    # this method is attached to the Accessor class
    def tag_locator (self, enforce=False):
        return self.locate_or_create_tag (tagname=tagname,
                                          category=category,
                                          description=description,
                                          roles=set_roles,
                                          enforce=enforce)

    # attach it to the Accessor class
    Accessor.register_tag_locator(locator_name,tag_locator)

    # body of the get method
    def get_call (self, auth, id_or_name):
        # locate the tag, see above
        tag_locator = Accessor.retrieve_tag_locator(locator_name)
        tag_type = tag_locator(AccessorSingleton(self.api))
        tag_type_id=tag_type['tag_type_id']

        filter = {'tag_type_id':tag_type_id}
        if isinstance (id_or_name,int):
            filter[primary_key]=id_or_name
        else:
            filter[secondary_key]=id_or_name
        joins = joins_class (self.api,filter,['value'])
        if not joins:
            # xxx - we return None even if id_or_name is not valid
            return None
        else:
            return joins[0]['value']

    # attach it
    setattr (get_class,"call",get_call)

    # body of the set method
    def set_call (self, auth, id_or_name, value):
        # locate the object
        if isinstance (id_or_name, int):
            filter={primary_key:id_or_name}
        else:
            filter={secondary_key:id_or_name}
# we need the full monty b/c of the permission system
#        objs = table_class(self.api, filter,[primary_key,secondary_key])
        objs = table_class(self.api, filter)
        if not objs:
            raise PLCInvalidArgument, "Cannot set tag on %s %r"%(objclass.__name__,id_or_name)
        # the object being tagged
        obj=objs[0]
        primary_id = obj[primary_key]

        # locate the tag, see above
        tag_locator = Accessor.retrieve_tag_locator(locator_name)
        tag_type = tag_locator(AccessorSingleton(self.api))
        tag_type_id = tag_type['tag_type_id']

        # check authorization
        if not hasattr(objclass,'caller_may_write_tag'):
            raise PLCAuthenticationFailure, "class %s misses method caller_may_write_tag"%objclass.__name__
        obj.caller_may_write_tag (self.api,self.caller,tag_type)

        # locate the join object (e.g. NodeTag or similar)
        filter = {'tag_type_id':tag_type_id}
        if isinstance (id_or_name,int):
            filter[primary_key]=id_or_name
        else:
            filter[secondary_key]=id_or_name
        joins = joins_class (self.api,filter)
        # setting to something non void
        if value is not None:
            if not joins:
                join = join_class (self.api)
                join['tag_type_id']=tag_type_id
                join[primary_key]=primary_id
                join['value']=value
                join.sync()
            else:
                joins[0]['value']=value
                joins[0].sync()
        # providing an empty value means clean up
        else:
            if joins:
                join=joins[0]
                join.delete()
        # log it
        self.event_objects= { objclass.__name__ : [primary_id] }
        self.message=objclass.__name__
        if secondary_key in objs[0]:
            self.message += " %s "%objs[0][secondary_key]
        else:
            self.message += " %d "%objs[0][primary_key]
        self.message += "updated"
        return value

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

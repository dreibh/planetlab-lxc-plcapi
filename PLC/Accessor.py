#
# Thierry Parmentelat - INRIA
#
#
# just a placeholder for storing accessor-related tag checkers
# this is filled by the accessors factory
#
# NOTE. If you ever come to manually delete a TagType that was created
# by the Factory, you need to restart your python instance / web server
# as the cached information then becomes wrong

from PLC.Debug import log 

from PLC.TagTypes import TagTypes, TagType
from PLC.Roles import Roles, Role

# implementation
class Accessor (object) :
    """This is placeholder for storing accessor-related tag checkers.
Methods in this class are defined by the accessors factory

This is implemented as a singleton, so we can cache results over time"""

    _instance = None

    tag_locators={}

    def __init__ (self, api):
        self.api=api
        # 'tagname'=>'tag_id'
        self.cache={}
        self.hash_name_to_role=dict ( [ (role['name'],role) for role in Roles(api)] )

    def has_cache (self,tagname): return self.cache.has_key(tagname)
    def get_cache (self,tagname): return self.cache[tagname]
    def set_cache (self,tagname,tag_type): self.cache[tagname]=tag_type

    def locate_or_create_tag (self, tagname, category, description, roles, enforce=False):
        "search tag type from tagname & create if needed"

        # cached ?
        if self.has_cache (tagname):
            return self.get_cache(tagname)
        # search
        tag_types = TagTypes (self.api, {'tagname':tagname})
        if tag_types:
            tag_type = tag_types[0]
            # enforce should only be set by the 'service plc start accessors' sequence
            if enforce:
                try:
                    tag_type.update({'category':category,'description':description})
                    tag_type.sync()
                    roles_to_add = set(roles).difference(set(tag_type['roles']))
                    for rolename in roles_to_add:
                        tag_type.add_role(self.hash_name_to_role[rolename])
                    roles_to_delete = set(tag_type['roles']).difference(set(roles))
                    for rolename in roles_to_delete:
                        tag_type.remove_role(self.hash_name_to_role[rolename])
                except:
                    # this goes in boot.log ...
                    print >> log, "WARNING, Could not enforce tag type, tagname=%s\n"%tagname
                    traceback.print_exc(file=log)
                    
        else:
            # not found: create it
            tag_type_fields = {'tagname':tagname,
                               'category' :  category,
                               'description' : description}
            tag_type = TagType (self.api, tag_type_fields)
            tag_type.sync()
            for role in roles:
                try: 
                    role_obj=Roles (self.api, role)[0]
                    tag_type.add_role(role_obj)
                except:
                    # xxx todo find a more appropriate way of notifying this
                    print "Accessor.locate_or_create_tag: Could not add role %r to tag_type %s"%(role,tagname)
        self.set_cache(tagname,tag_type)
        return tag_type

    # a locator is a function that retrieves - or creates - a tag_type instance
    @staticmethod
    def register_tag_locator (name, tag_locator):
        Accessor.tag_locators[name]=tag_locator

    @staticmethod
    def retrieve_tag_locator (name):
        return Accessor.tag_locators[name]
    
    # this is designed to be part of the 'service plc start' sequence
    # it ensures the creation of all the tagtypes defined 
    # in the various accessors, and enforces consistency to the DB
    # it's not easy to have define_accessors do this because at
    # load-time as we do not have an instance of API yet
    def run_all_tag_locators (self):
        for (name, tag_locator) in Accessor.tag_locators.items():
            tag_locator(self,enforce=True)

####################
# make it a singleton so we can cache stuff in there over time
def AccessorSingleton (api):
    if not Accessor._instance:
        Accessor._instance = Accessor(api)
    return Accessor._instance

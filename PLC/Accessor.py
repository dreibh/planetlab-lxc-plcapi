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

from PLC.TagTypes import TagTypes, TagType
from PLC.Roles import Roles, Role

# implementation
class Accessor (object) :
    """This is placeholder for storing accessor-related tag checkers.
Methods in this class are defined by the accessors factory

This is implemented as a singleton, so we can cache results over time"""

    _instance = None

    def __init__ (self, api):
        self.api=api
        # 'tagname'=>'tag_id'
        self.cache={}

    def has_cache (self,tagname): return self.cache.has_key(tagname)
    def get_cache (self,tagname): return self.cache[tagname]
    def set_cache (self,tagname,tag_id): self.cache[tagname]=tag_id

    def locate_or_create_tag (self, tagname, category, description, roles):
        "search tag type from tagname & create if needed"

        # cached ?
        if self.has_cache (tagname):
            return self.get_cache(tagname)
        # search
        tag_types = TagTypes (self.api, {'tagname':tagname})
        if tag_types:
            tag_type = tag_types[0]
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
        tag_type_id = tag_type['tag_type_id']
        self.set_cache(tagname,tag_type_id)
        return tag_type_id


####################
# make it a singleton so we can cache stuff in there over time
def AccessorSingleton (api):
    if not Accessor._instance:
        Accessor._instance = Accessor(api)
    return Accessor._instance

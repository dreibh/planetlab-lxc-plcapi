# $Id$
# $URL$
#
# Thierry Parmentelat - INRIA
#
#
# just a placeholder for storing accessor-related tag checkers
# this is filled by the accessors factory

from PLC.TagTypes import TagTypes, TagType

# implementation
class Accessor (object) :
    """This is placeholder for storing accessor-related tag checkers
methods in this class are defined by the accessors factory

This is implemented as a singleton, so we can cache results over time"""

    _instance = None

    def __init__ (self, api):
        self.api=api
        # 'tagname'=>'tag_id'
        self.cache={}

    def has_cache (self,tagname): return self.cache.has_key(tagname)
    def get_cache (self,tagname): return self.cache[tagname]
    def set_cache (self,tagname,tag_id): self.cache[tagname]=tag_id

    def locate_or_create_tag (self,tagname,category, description, min_role_id):
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
                               'description' : description,
                               'min_role_id': min_role_id}
            tag_type = TagType (self.api, tag_type_fields)
            tag_type.sync()
        tag_type_id = tag_type['tag_type_id']
        self.set_cache(tagname,tag_type_id)
        return tag_type_id


####################
# make it a singleton so we can cache stuff in there over time
def AccessorSingleton (api):
    if not Accessor._instance:
        Accessor._instance = Accessor(api)
    return Accessor._instance

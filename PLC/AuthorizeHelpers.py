#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Persons import Persons,Person
from PLC.Sites import Sites,Site
from PLC.Nodes import Nodes,Node

class AuthorizeHelpers:

    @staticmethod
    def person_tag_type_common_roles (api, person, tag_type):
        return list (set(person['roles']).intersection(set(tag_type['roles'])))

    @staticmethod
    def caller_may_access_tag_type (api, caller, tag_type):
        if isinstance(caller,Person):
            return len(AuthorizeHelpers.person_tag_type_common_roles(api,caller,tag_type))!=0
        elif isinstance(caller,Node):
            return 'node' in tag_type['roles']
        else:
            raise PLCInvalidArgument, "caller_may_access_tag_type - unexpected arg"

    @staticmethod
    def person_may_access_person (api, caller_person, subject_person):
        # keep it simple for now - could be a bit more advanced for PIs maybe
        try:    return caller_person['person_id'] == subject_person['person_id']
        except: return False

    @staticmethod
    def person_in_site (api, person, site):
        return site['site_id'] in person['site_ids']

    @staticmethod
    def person_in_slice (api, caller_person, slice):
        return caller_person['person_id'] in slice['person_ids']

    @staticmethod
    def slice_in_site (api, slice, site):
        return slice['site_id']==site['site_id']

    @staticmethod
    def node_id_in_slice (api, node_id_or_hostname, slice):
        if isinstance (node_id_or_hostname,int):
            return node_id_or_hostname in slice['node_ids']
        else:
            try:   return Nodes(api,node_id_or_hostname)[0]['node_id'] in slice['node_ids']
            except:return False

    @staticmethod
    def node_id_in_site (api, node_id_or_hostname, site):
        if isinstance (node_id_or_hostname,int):
            return node_id_or_hostname in site['node_ids']
        else:
            try:   return Nodes(api,node_id_or_hostname)[0]['node_id'] in site['node_ids']
            except:return False


    @staticmethod
    def node_match_id (api, node, node_id_or_hostname):
        if isinstance (node_id_or_hostname,int):
            return node['node_id']==node_id_or_hostname
        else:
            return node['hostname']==node_id_or_hostname

    @staticmethod
    def interface_belongs_to_person (api,interface, person):
        try:
            node=Nodes(api,[interface['node_id']])[0]
            return AuthorizeHelpers.node_belongs_to_person (api, node, person)
        except:
            return False

    @staticmethod
    def node_belongs_to_person (api, node, person):
        try:
            site=Sites(api,[node['site_id']])[0]
            return AuthorizeHelpers.person_in_site (api, person, site)
        except:
            import traceback
            return False

    # does the slice belong to the site that the (pi) user is in ?
    @staticmethod
    def slice_belongs_to_pi (api, slice, pi):
        return slice['site_id'] in pi['site_ids']


# authorization method - check if a given caller can set tag on this object
# called in {Add,Update,Delete}NodeTags methods and in the accessors factory
def caller_may_write_node_tag (node, api, caller, tag_type):
    if 'admin' in caller['roles']:
        pass
    elif not AuthorizeHelpers.caller_may_access_tag_type (api, caller, tag_type):
        raise PLCPermissionDenied, "Role mismatch for writing tag %s"%(tag_type['tagname'])
    elif AuthorizeHelpers.node_belongs_to_person (api, node, caller):
        pass
    else:
        raise PLCPermissionDenied, "Writing node tag: must belong in the same site as %s"%\
            (node['hostname'])

setattr(Node,'caller_may_write_tag',caller_may_write_node_tag)
        

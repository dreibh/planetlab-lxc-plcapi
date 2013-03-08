#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Persons import Persons,Person
from PLC.Sites import Sites,Site
from PLC.Nodes import Nodes,Node
from PLC.Interfaces import Interfaces,Interface
from PLC.Slices import Slices,Slice

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
    def node_in_slice (api, caller_node, slice):
        return caller_node['node_id'] in slice['node_ids']

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

    @staticmethod
    def caller_is_node (api, caller, node):
        return 'node_id' in caller and caller['node_id']==node['node_id']


# authorization methods - check if a given caller can set tag on this object
# called in {Add,Update,Delete}<Class>Tags methods, and in the accessors created in factory
# attach these as <Class>.caller_may_write_tag so accessors can find it

def caller_may_write_node_tag (node, api, caller, tag_type):
    if 'roles' in caller and 'admin' in caller['roles']:
        pass
    elif not AuthorizeHelpers.caller_may_access_tag_type (api, caller, tag_type):
        raise PLCPermissionDenied, "Role mismatch for writing tag %s"%(tag_type['tagname'])
    elif AuthorizeHelpers.node_belongs_to_person (api, node, caller):
        pass
    elif AuthorizeHelpers.caller_is_node (api, caller, node):
        pass
    else:
        raise PLCPermissionDenied, "Writing node tag: must belong in the same site as %s"%\
            (node['hostname'])

setattr(Node,'caller_may_write_tag',caller_may_write_node_tag)
        

def caller_may_write_interface_tag (interface, api, caller, tag_type):
    if 'roles' in caller and 'admin' in caller['roles']:
        pass
    elif not AuthorizeHelpers.caller_may_access_tag_type (api, caller, tag_type):
        raise PLCPermissionDenied, "Role mismatch for writing tag %s"%(tag_type['tagname'])
    elif AuthorizeHelpers.interface_belongs_to_person (api, interface, caller):
        pass
    else:
        raise PLCPermissionDenied, "Writing interface tag: must belong in the same site as %s"%\
            (interface['ip'])
        
setattr(Interface,'caller_may_write_tag',caller_may_write_interface_tag)
        

def caller_may_write_site_tag (site, api, caller, tag_type):
    if 'roles' in caller and 'admin' in caller['roles']:
        pass
    elif not AuthorizeHelpers.caller_may_access_tag_type (api, caller, tag_type):
        raise PLCPermissionDenied, "Role mismatch for writing tag %s"%(tag_type['tagname'])
    elif AuthorizeHelpers.person_in_site (api, caller, site):
        pass
    else:
        raise PLCPermissionDenied, "Writing site tag: must be part of site"%site['login_base']

setattr(Site,'caller_may_write_tag',caller_may_write_site_tag)


def caller_may_write_person_tag (person, api, caller, tag_type):
    if 'roles' in caller and 'admin' in caller['roles']:
        pass
    # user can change tags on self
    elif AuthorizeHelpers.person_may_access_person (api, caller, person):
        pass
    else:
        raise PLCPermissionDenied, "Writing person tag: you can only change your own tags"

setattr(Person,'caller_may_write_tag',caller_may_write_person_tag)


def caller_may_write_slice_tag (slice, api, caller, tag_type, node_id_or_hostname=None, nodegroup_id_or_name=None):
    granted=False
    reason=""
    if 'roles' in caller and 'admin' in caller['roles']:
        granted=True
    # does caller have right role(s) ? this knows how to deal with caller being a node
    elif not AuthorizeHelpers.caller_may_access_tag_type (api, caller, tag_type):
        reason="caller may not access this tag type"
        granted=False
    # node callers: check the node is in the slice
    elif isinstance(caller, Node): 
        # nodes can only set their own sliver tags
        if node_id_or_hostname is None: 
            reason="wrong node caller"
            granted=False
        elif not AuthorizeHelpers.node_match_id (api, caller, node_id_or_hostname):
            reason="node mismatch"
            granted=False
        elif not AuthorizeHelpers.node_in_slice (api, caller, slice):
            reason="slice not in node"
            granted=False
        else:
            granted=True
    # caller is a non-admin person
    else:
        # only admins can handle slice tags on a nodegroup
        if nodegroup_id_or_name:
            raise PLCPermissionDenied, "Cannot set slice tag %s on nodegroup - restricted to admins"%\
                (tag_type['tagname'])
        # if a node is specified it is expected to be in the slice
        if node_id_or_hostname:
            if not AuthorizeHelpers.node_id_in_slice (api, node_id_or_hostname, slice):
                raise PLCPermissionDenied, "%s, node must be in slice when setting sliver tag"
        # try all roles to find a match - tech are ignored b/c not in AddSliceTag.roles anyways
        for role in AuthorizeHelpers.person_tag_type_common_roles(api,caller,tag_type):
            reason="user not in slice; or slice does not belong to pi's site"
            # regular users need to be in the slice
            if role=='user':
                if AuthorizeHelpers.person_in_slice(api, caller, slice):
                    granted=True ; break
            # for convenience, pi's can tweak all the slices in their site
            elif role=='pi':
                if AuthorizeHelpers.slice_belongs_to_pi (api, slice, caller):
                    granted=True ; break
    if not granted:
#        try: print "DEBUG: caller=%s"%caller
#        except: pass
        raise PLCPermissionDenied, "Cannot write slice tag %s - %s"%(tag_type['tagname'],reason)

setattr(Slice,'caller_may_write_tag',caller_may_write_slice_tag)



#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Persons import Persons,Person
from PLC.Sites import Sites,Site
from PLC.Nodes import Nodes,Node

class AuthorizeHelpers:

    @staticmethod
    def interface_belongs_to_person (api,interface, person):
        try:
            node=Nodes(api,[interface['node_id']])[0]
            return AuthorizeHelpers.node_belong_to_person (api, node, person)
        except:
            return False

    @staticmethod
    def node_belongs_to_person (api, node, person):
        try:
            site=Sites(api,[node['site_id']])[0]
            return AuthorizeHelpers.person_belongs_to_site (api, person, site)
        except:
            return False

    @staticmethod
    def person_belongs_to_site (api, person, site):
        return site['site_id'] in person['site_ids']

    @staticmethod
    def caller_may_access_tag_type (api, caller, tag_type):
        if isinstance(caller,Person):
            return len(set(caller['roles']).intersection(set(tag_type['roles'])))!=0
        elif isinstance(caller,Node):
            return 'node' in tag_type['roles']
        else:
            raise PLCInvalidArgument, "caller_may_access_tag_type - unexpected arg"

    @staticmethod
    def person_access_person (api, caller_person, subject_person):
        # keep it simple for now - could be a bit more advanced for PIs maybe
        try:    return caller_person['person_id'] == subject_person['person_id']
        except: return False

    @staticmethod
    def person_in_slice (api, caller_person, slice):
        return caller_person['person_id'] in slice['person_ids']

    @staticmethod
    def node_in_slice (api, caller_node, slice):
        return caller_node['node_id'] in slice['node_ids']

    @staticmethod
    def node_id_or_hostname_in_slice (api, node_id_or_hostname, slice):
        if isinstance (node_id_or_hostname,int):
            return node_id_or_hostname in slice['node_ids']
        else:
            try:   return Nodes(api,node_id_or_hostname_in_slice)[0]['node_id'] in slice['node_ids']
            except:return False



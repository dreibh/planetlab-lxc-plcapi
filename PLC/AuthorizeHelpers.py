#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *

class AuthorizeHelpers:

    @staticmethod
    def interface_belongs_to_person (api,interface, person):
        try:
            node=api.GetNodes(interface['node_id'])[0]
            return node_belong_to_person (api, node, person)
        except:
            return False

    @staticmethod
    def node_belongs_to_person (api, node, person):
        try:
            site=api.GetSites(node['site_id'])[0]
            return person_belongs_to_site (api, person, site)
        except:
            return False

    @staticmethod
    def person_belongs_to_site (api, person, site):
        return site['site_id'] in person['site_ids']

    @staticmethod
    def person_access_tag_type (api, person, tag_type):
        return len(set(person['roles']).intersection(set(tag_type['roles'])))!=0

    @staticmethod
    def person_access_person (api, caller_person, subject_person):
        # keep it simple for now - could be a bit more advanced for PIs maybe
        return caller_person['person_id'] == subject_person['person_id']




from types import StringTypes
import traceback
from types import StringTypes
import traceback

class SFA:
    
    def __init__(self):
        try:
            from sfa.plc.sfaImport import sfaImport
            from sfa.plc.api import GeniAPI
            from sfa.util.debug import log 
            self.log = log
            self.sfa = sfaImport()
            geniapi = GeniAPI()
            self.plcapi = geniapi.plshell
            self.auth = geniapi.plauth
        except:
            traceback.print_exc(file = self.log)

        if self.gimport.level1_auth:
            self.authority = self.gimport.level1_auth
        else:
            self.authority = self.gimport.root_auth


    def get_login_base(site_id):
        sites = self.plcapi.GetSites(self.auth, [site_id], ['login_base'])
        login_base = sites

    def get_login_bases(self, object):
        login_bases = []
        site_ids = []
        
        # get the site_ids
        if object.has_key('site_id') and object['site_id']:
            site_ids.append(object['site_id'])
        elif object.has_key('site_ids') and object['site_ids']:
            site_ids.extend(object['site_ids'])
        else:
            raise Exception

        # get the login bases
        for site_id in site_ids:
            login_bases.append(self.get_login_base(site_id))

        return login_bases

    def update_record(self, object, type, login_bases = None):
        try:
            # determine this objects site and login_base
            if not login_bases:
                login_bases = self.get_login_bases(object)

            if isinstance(login_bases, StringTypes):
                login_bases = [login_bases]

            for login_base in login_bases:
                login_base = self.sfa.cleanup_string(login_base)
                parent_hrn = self.authority + "." + login_base
                if type in ['person']:
                    self.sfa.import_person(parent_hrn, object)
                elif type in ['slice']:
                    self.sfa.import_slice(parent_hrn, object)
                elif type in ['node']:
                    self.sfa.import_node(parent_hrn, object)
                elif type in ['site']:
                    self.sfa.import_site(self.authority, object)
        except Exception, e:
            id = None
            keys = ['name', 'hostname', 'email', 'login_base']
            for key in keys:
                if object.has_key(key):
                    id = object[key]
            traceback.print_exc(file = self.log)
            print >> self.log, "Error importing %s record for %s into geni db: %s" % \
                  (type, id, e.message)

    def delete_record(self, object, type, login_base = None):
        if not login_bases:
            login_bases = get_login_bases(object)

        for login_base in login_bases:
            login_base = self.sfa.cleanup_string(login_base)
            parent_hrn = self.authority + "." + login_base
            self.sfa.delete_record(parent_hrn, object, type)

    def update_site(self, site, login_base = None):
        self.update_record(site, 'site', login_base)

    def update_site(self, site, login_base = None):
        self.update_record(site, 'site', login_base)

    def update_node(self, node, login_base = None):
        self.update_record(node, 'node', login_base)

    def update_slice(self, slice, login_base = None):
        self.update_record(slice, 'slice', login_base)

    def update_person(self, person, login_base = None):
        self.update_record(person, 'person', login_base)

    def delete_site(self, site, login_base = None):
        site_name = site['login_base']
        hrn = parent_hrn + site_name
        self.delete_record(site, 'site', login_base)

    def delete_node(self, node, login_base = None):
        self.delete_record(node, 'node', login_base)

    def delete_slice(self, slice, login_base = None):
        self.delete_record(slice, 'slice', login_base)

    def delete_person(self, person, login_base = None):
        self.delete_record(person, 'person', login_base)         

import traceback
from types import StringTypes
from PLC.Sites import Sites
try:
    from sfa.plc.sfaImport import sfaImport, cleanup_string
    from sfa.util.debug import log
    packages_imported = True
except:
    packages_imported = False
    

def wrap_exception(method):
    def wrap(*args, **kwds):
        try:
            return method(*args, **kwds)
        except:
            pass
            #traceback.print_exc()
    return wrap

def required_packages_imported(method):
    def wrap(*args, **kwds):
        if packages_imported:
            return method(*args, **kwds)
        else:
            return
    return wrap         

class SFA:
    
    @wrap_exception
    @required_packages_imported
    def __init__(self, api):
        
        self.api = api
        self.sfa = sfaImport()

        if self.sfa.level1_auth:
            self.authority = self.sfa.level1_auth
        else:
            self.authority = self.sfa.root_auth


    def get_login_base(self, site_id):
        sites = Sites(self.api, [site_id], ['login_base'])
        login_base = sites[0]['login_base']
        return login_base
        

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

    @wrap_exception
    @required_packages_imported
    def update_record(self, object, type, login_bases = None):
        try:
            # determine this objects site and login_base
            if not login_bases:
                login_bases = self.get_login_bases(object)

            if isinstance(login_bases, StringTypes):
                login_bases = [login_bases]

            for login_base in login_bases:
                login_base = cleanup_string(login_base)
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
            traceback.print_exc(file = log)
            print >> log, "Error importing %s record for %s into geni db: %s" % \
                  (type, id, e.message)

    @wrap_exception
    @required_packages_imported
    def delete_record(self, object, type, login_base = None):

        if not login_base:
            login_bases = self.get_login_bases(object)
        else:
            login_bases = [login_base]

        for login_base in login_bases:
            login_base = cleanup_string(login_base)
            parent_hrn = self.authority + "." + login_base
            self.sfa.delete_record(parent_hrn, object, type)

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

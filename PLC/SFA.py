import traceback
from types import StringTypes
from PLC.Sites import Sites
try:
    from sfa.plc.api import GeniAPI
    from sfa.plc.sfaImport import cleanup_string
    from sfa.server.registry import Registries
    from sfa.util.record import *
    from sfa.trust.hierarchy import *
    from sfa.util.misc import *
    packages_imported = True
except:
    packages_imported = False
    
def wrap_exception(method):
    def wrap(*args, **kwds):
        try:
            return method(*args, **kwds)
        except:
            traceback.print_exc()
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
        
        # Get the path to the sfa server key/cert files from 
        # the sfa hierarchy object
        sfa_hierarchy = Hierarchy()
        sfa_key_path = sfa_hierarchy.basedir
        key_file = os.path.join(sfa_key_path, "server.key")
        cert_file = os.path.join(sfa_key_path, "server.cert")
    
        # get a connection to our local sfa registry
        # and a valid credential
        self.sfa_api = GeniAPI(key_file = key_file, cert_file = cert_file)
        self.sfa_api.interface = "other"
        registries = Registries(self.sfa_api)
        self.registry = registries[self.sfa_api.hrn]
        self.credential = self.sfa_api.getCredential()
        self.authority = self.sfa_api.hrn
        

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

    def get_object_hrn(self, type, object, authority, login_base):
        parent_hrn = authority + "." + login_base 
        if type in ['person', 'user']:
            name_parts = object['email'].split("@")
            hrn = parent_hrn + "." + name_parts[:1]
        
        elif type in ['slice']:
            name_parts = object['name'].split("_")
            hrn = parent_hrn + "." + name_parts[-1:]
        
        elif type in ['node']:
            hrn = hostname_to_hrn(self.authority, login_base, object['hostname'])
        
        elif type in ['site', 'authority']:
            hrn = parent_hrn
        
        else:
            raise Exception, "Invalid record type %(type)s" % locals()

        return hrn

    @wrap_exception
    @required_packages_imported
    def update_record(self, object, type, login_bases = None):
        # determine this objects site and login_base
        if not login_bases:
            login_bases = self.get_login_bases(object)

        if isinstance(login_bases, StringTypes):
            login_bases = [login_bases]

        for login_base in login_bases:
            login_base = cleanup_string(login_base)
            parent_hrn = self.authority + "." + login_base
                
            # set the object hrn, tpye and create the sfa record 
            # object 
            object['hrn'] = self.get_object_hrn(type, object, self.authority, login_base)   
            if type in ['person', 'user']:
                object['type'] = 'user'
                record = UserRecord(dict=object)

            elif type in ['slice']:
                object['type'] = 'slice'
                record = SliceRecord(dict=object)

            elif type in ['node']:
                object['type'] = 'node'
                record = NodeRecord(dict=object)
    
            elif type in ['site']:
                object['type'] = 'authority'
                record = AuthorityRecord(dict=object)

            else:
                raise Exception, "Invalid record type %(type)s" % locals()

            # add the record to sfa
            self.registry.register(self.credential, record)

    @wrap_exception
    @required_packages_imported
    def delete_record(self, object, type, login_base = None):
        if type in ['person']:
            type = 'user'
        elif type in ['site']:
            type = 'authority'
        
        if type not in ['user', 'slice', 'node', 'authority']:
            raise Exception, "Invalid type %(type)s" % locals()    
     
        if not login_base:
            login_bases = self.get_login_bases(object)
        else:
            login_bases = [login_base]

        for login_base in login_bases:
            login_base = cleanup_string(login_base)
            hrn = self.get_object_hrn(type, object, self.authority, login_base)
            self.registry.remove(self.credential, type, hrn) 


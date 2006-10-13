from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Addresses import Address, Addresses
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class GetAddresses(Method):
    """
    Get an array of structs containing the addresses of the specified
    site. If address_id_list is specified, only the specified
    addresses will be queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        [Address.fields['address_id']],
        ]

    returns = [Address.fields]

    def call(self, auth, site_id_or_login_base, address_id_list = None):
        sites = Sites(self.api, [site_id_or_login_base]).values()
        if not sites:
            raise PLCInvalidArgument, "No such site"
        site = sites[0]

        if address_id_list is None:
            address_id_list = site['address_ids']
        else:
            if set(address_id_list).intersection(site['address_ids']) != \
               set(address_id_list):
                raise PLCInvalidArgument, "Invalid address ID(s)"

        addresses = Addresses(self.api, address_id_list).values()
	
	# Turn each address into a real dict
	addresses = [dict(address.items) for address in addresses]

        return addresses

#
# Thierry Parmentelat - INRIA
#
# $Revision: 88 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

from PLC.NodeNetworkSettings import NodeNetworkSetting, NodeNetworkSettings
from PLC.Sites import Site, Sites
from PLC.NodeNetworks import NodeNetwork, NodeNetworks

class GetNodeNetworkSettings(Method):
    """
    Returns an array of structs containing details about
    nodenetworks and related settings.

    If nodenetwork_setting_filter is specified and is an array of
    nodenetwork setting identifiers, only nodenetwork settings matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed([NodeNetworkSetting.fields['nodenetwork_setting_id']],
              Parameter(int,"Nodenetwork setting id"),
              Filter(NodeNetworkSetting.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [NodeNetworkSetting.fields]
    

    def call(self, auth, nodenetwork_setting_filter = None, return_fields = None):

        nodenetwork_settings = NodeNetworkSettings(self.api, nodenetwork_setting_filter, return_fields)

        return nodenetwork_settings

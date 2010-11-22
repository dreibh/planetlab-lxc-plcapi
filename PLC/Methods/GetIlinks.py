#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.Ilinks import Ilink, Ilinks
from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes

class GetIlinks(Method):
    """
    Returns an array of structs containing details about
    nodes and related tags.

    If ilink_filter is specified and is an array of
    ilink identifiers, only ilinks matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed([Ilink.fields['ilink_id']],
              Parameter(int,"ilink id"),
              Filter(Ilink.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [Ilink.fields]


    def call(self, auth, ilink_filter = None, return_fields = None):

        ilinks = Ilinks(self.api, ilink_filter, return_fields)

        return ilinks

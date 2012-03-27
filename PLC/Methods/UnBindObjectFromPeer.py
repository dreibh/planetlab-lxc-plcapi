from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Persons import Persons
from PLC.Sites import Sites
from PLC.Nodes import Nodes
from PLC.Slices import Slices
from PLC.Keys import Keys
from PLC.Peers import Peers
from PLC.Faults import *

class UnBindObjectFromPeer(Method):
    """
    This method is a hopefully temporary hack to let the sfa correctly
    detach the objects it creates from a remote peer object. This is
    needed so that the sfa federation link can work in parallel with
    RefreshPeer, as RefreshPeer depends on remote objects being
    correctly marked.

    UnBindObjectFromPeer is allowed to admins only.
    """

    roles = ['admin']

    known_types = ['site','person','slice','node','key']
    types_doc = ",".join(["'%s'"%type for type in known_types])

    accepts = [
        Auth(),
        Parameter(str,"Object type, among "+types_doc),
        Parameter(int,"object_id"),
        Parameter(str,"peer shortname"),
        Parameter(int,"remote object_id, set to 0 if unknown"),
        ]

    returns = Parameter (int, '1 if successful')

    def locate_object (self, object_type, object_id):
        # locate e.g. the Nodes symbol
        class_obj = globals()[object_type.capitalize()+'s']
        id_name=object_type+'_id'
        # invoke e.g. Nodes ({'node_id':node_id})
        objs=class_obj(self.api,{id_name:object_id})
        if len(objs) != 1:
            raise PLCInvalidArgument,"Cannot locate object, type=%s id=%d"%\
                (type,object_id)
        return objs[0]


    def call(self, auth, object_type, object_id, shortname):

        object_type = object_type.lower()
        if object_type not in self.known_types:
            raise PLCInvalidArgument, 'Unrecognized object type %s'%object_type

        peers=Peers(self.api,{'shortname':shortname.upper()})
        if len(peers) !=1:
            raise PLCInvalidArgument, 'No such peer with shortname %s'%shortname

        peer=peers[0]
        object = self.locate_object (object_type, object_id)
        remover_name = 'remove_'+object_type
        remove_function = getattr(type(peer),remover_name)
        remove_function(peer,object)

        return 1

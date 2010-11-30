from PLC.Method import Method
from PLC.Auth import Auth
from PLC.Faults import *
from PLC.Parameter import *
from PLC.Nodes import Node, Nodes

from PLC.Accessors.Accessors_standard import *                  # import node accessors

class GetNodeFlavour(Method):
    """
    Returns detailed information on a given node's flavour, i.e. its
    base installation.

    This depends on the global PLC settings in the PLC_FLAVOUR area,
    optionnally overridden by any of the following tags if set on that node:

    'arch', 'pldistro', 'fcdistro',
    'deployment', 'extensions',
    """

    roles = ['admin', 'user', 'node']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        ]

    returns = {
        'nodefamily' : Parameter (str, "the nodefamily this node should be based upon"),
        'fcdistro': Parameter (str, "the fcdistro this node should be based upon"),
        'extensions' : [ Parameter (str, "extensions to add to the base install") ],
        'plain' : Parameter (bool, "use plain bootstrapfs image if set (for tests)" ) ,
        }


    ########## nodefamily
    def nodefamily (self, auth, node_id, fcdistro, arch):

        # the deployment tag, if set, wins
        # xxx Thierry: this probably is wrong; we need fcdistro to be set anyway
        # for generating the proper yum config....
        deployment = GetNodeDeployment (self.api,self.caller).call(auth,node_id)
        if deployment: return deployment

        pldistro = GetNodePldistro (self.api,self.caller).call(auth, node_id)
        if not pldistro:
            pldistro = self.api.config.PLC_FLAVOUR_NODE_PLDISTRO
            SetNodePldistro(self.api).call(auth,node_id,pldistro)

        # xxx would make sense to check the corresponding bootstrapfs is available
        return "%s-%s-%s"%(pldistro,fcdistro,arch)

    def extensions (self, auth, node_id, fcdistro, arch):
        try:
            return [ "%s-%s-%s"%(e,fcdistro,arch) for e in GetNodeExtensions(self.api,self.caller).call(auth,node_id).split() ]
        except:
            return []

    def plain (self, auth, node_id):
        return not not GetNodePlainBootstrapfs(self.api,self.caller).call(auth,node_id)

    def call(self, auth, node_id_or_name):
        # Get node information
        nodes = Nodes(self.api, [node_id_or_name])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id_or_name
        node = nodes[0]
        node_id = node['node_id']

        arch = GetNodeArch (self.api,self.caller).call(auth,node_id)
        # if not set, use the global default and tag the node, in case the global default changes later on
        if not arch:
            arch = self.api.config.PLC_FLAVOUR_NODE_ARCH
            SetNodeArch (self.api).call(auth,node_id,arch)

        fcdistro = GetNodeFcdistro (self.api,self.caller).call(auth, node_id)
        if not fcdistro:
            fcdistro = self.api.config.PLC_FLAVOUR_NODE_FCDISTRO
            SetNodeFcdistro (self.api).call (auth, node_id, fcdistro)

        # xxx could use some sanity checking, and could provide fallbacks
        return { 'nodefamily' : self.nodefamily(auth,node_id, fcdistro, arch),
                 'fcdistro' : fcdistro,
                 'extensions' : self.extensions(auth,node_id, fcdistro, arch),
                 'plain' : self.plain(auth,node_id),
                 }

import traceback

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
    'deployment', 'extensions', 'virt', 
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
    def nodefamily (self, auth, node_id, fcdistro, pldistro, arch):

        # the deployment tag, if set, wins
        # xxx Thierry: this probably is wrong; we need fcdistro to be set anyway
        # for generating the proper yum config....
        deployment = GetNodeDeployment (self.api,self.caller).call(auth,node_id)
        if deployment: return deployment

        # xxx would make sense to check the corresponding bootstrapfs is available
        return "%s-%s-%s"%(pldistro,fcdistro,arch)

    ##########
    # parse PLC_FLAVOUR_VIRT_MAP 
    known_virts=['vs','lxc']
    default_virt='vs'
    def virt_from_virt_map (self, node_fcdistro):
        map={}
        try:
            assigns=[x.strip() for x in self.api.config.PLC_FLAVOUR_VIRT_MAP.split(';')]
            for assign in assigns:
                (left,right)=[x.strip() for x in assign.split(':')]
                if right not in GetNodeFlavour.known_virts:
                    print "GetNodeFlavour, unknown 'virt' %s - ignored" % right
                    continue
                for fcdistro in [ x.strip() for x in left.split(',')]:
                    map[fcdistro]=right
        except:
            print "GetNodeFlavour, issue with parsing PLC_FLAVOUR_VIRT_MAP=%s - returning '%s'"%\
                (self.api.config.PLC_FLAVOUR_VIRT_MAP,GetNodeFlavour.default_virt)
            traceback.print_exc()
            return GetNodeFlavour.default_virt
#        print 'virt_from_virt_map, using map',map
        if node_fcdistro in map:  return map[node_fcdistro]
        if 'default' in map: return map['default']
        return GetNodeFlavour.default_virt
            

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
            SetNodeArch (self.api,self.caller).call(auth,node_id,arch)

        fcdistro = GetNodeFcdistro (self.api,self.caller).call(auth, node_id)
        if not fcdistro:
            fcdistro = self.api.config.PLC_FLAVOUR_NODE_FCDISTRO
            SetNodeFcdistro (self.api,self.caller).call (auth, node_id, fcdistro)

        pldistro = GetNodePldistro (self.api,self.caller).call(auth, node_id)
        if not pldistro:
            pldistro = self.api.config.PLC_FLAVOUR_NODE_PLDISTRO
            SetNodePldistro(self.api,self.caller).call(auth,node_id,pldistro)

        virt = GetNodeVirt (self.api,self.caller).call(auth, node_id)
        if not virt:
            virt = self.virt_from_virt_map (fcdistro)
            # do not save in node - if a node was e.g. f14 and it gets set to f16
            # we do not want to have to re-set virt
            # SetNodeVirt (self.api, self.caller).call (auth, node_id, virt)

        # xxx could use some sanity checking, and could provide fallbacks
        return {
            'arch'      : arch,
            'fcdistro'  : fcdistro,
            'pldistro'  : pldistro,
            'virt'      : virt,
            'nodefamily': self.nodefamily(auth,node_id, fcdistro, pldistro, arch),
            'extensions': self.extensions(auth,node_id, fcdistro, arch),
            'plain'     : self.plain(auth,node_id),
            }

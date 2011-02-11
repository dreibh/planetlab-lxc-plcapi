import random
import base64
import os
import os.path
import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.InterfaceTags import InterfaceTag, InterfaceTags
from PLC.NodeTags import NodeTag, NodeTags

from PLC.Accessors.Accessors_standard import *                  # import node accessors

# could not define this in the class..
# create a dict with the allowed actions for each type of node
# reservable nodes being more recent, we do not support the floppy stuff anymore
allowed_actions = {
    'regular' :
    [ 'node-preview',
      'node-floppy',
      'node-iso',
      'node-usb',
      'generic-iso',
      'generic-usb',
      ],
    'reservable':
    [ 'node-preview',
      'node-iso',
      'node-usb',
      ],
    }

# compute a new key
def compute_key():
    # Generate 32 random bytes
    bytes = random.sample(xrange(0, 256), 32)
    # Base64 encode their string representation
    key = base64.b64encode("".join(map(chr, bytes)))
    # Boot Manager cannot handle = in the key
    # XXX this sounds wrong, as it might prevent proper decoding
    key = key.replace("=", "")
    return key

class GetBootMedium(Method):
    """
    This method is a redesign based on former, supposedly dedicated,
    AdmGenerateNodeConfFile

    As compared with its ancestor, this method provides a much more
    detailed interface, that allows to
    (*) either just preview the node config file -- in which case
        the node key is NOT recomputed, and NOT provided in the output
    (*) or regenerate the node config file for storage on a floppy
        that is, exactly what the ancestor method used todo,
        including renewing the node's key
    (*) or regenerate the config file and bundle it inside an ISO or USB image
    (*) or just provide the generic ISO or USB boot images
        in which case of course the node_id_or_hostname parameter is not used

    action is expected among the following string constants according the
    node type value:

    for a 'regular' node:
    (*) node-preview
    (*) node-floppy
    (*) node-iso
    (*) node-usb
    (*) generic-iso
    (*) generic-usb

    Apart for the preview mode, this method generates a new node key for the
    specified node, effectively invalidating any old boot medium.
    Note that 'reservable' nodes do not support 'node-floppy',
    'generic-iso' nor 'generic-usb'.

    In addition, two return mechanisms are supported.
    (*) The default behaviour is that the file's content is returned as a
        base64-encoded string. This is how the ancestor method used to work.
        To use this method, pass an empty string as the file parameter.

    (*) Or, for efficiency -- this makes sense only when the API is used
        by the web pages that run on the same host -- the caller may provide
        a filename, in which case the resulting file is stored in that location instead.
        The filename argument can use the following markers, that are expanded
        within the method
        - %d : default root dir (some builtin dedicated area under /var/tmp/)
               Using this is recommended, and enforced for non-admin users
        - %n : the node's name when this makes sense, or a mktemp-like name when
               generic media is requested
        - %s : a file suffix appropriate in the context (.txt, .iso or the like)
        - %v : the bootcd version string (e.g. 4.0)
        - %p : the PLC name
        - %f : the nodefamily
        - %a : arch
        With the file-based return mechanism, the method returns the full pathname
        of the result file;
        ** WARNING **
        It is the caller's responsability to remove this file after use.

    Options: an optional array of keywords.
        options are not supported for generic images
      Currently supported are
        - 'partition' - for USB actions only
        - 'cramfs'
        - 'serial' or 'serial:<console_spec>'
        console_spec (or 'default') is passed as-is to bootcd/build.sh
        it is expected to be a colon separated string denoting
        tty - baudrate - parity - bits
        e.g. ttyS0:115200:n:8
        - 'variant:<variantname>'
        passed to build.sh as -V <variant>
        variants are used to run a different kernel on the bootCD
        see kvariant.sh for how to create a variant
        - 'no-hangcheck' - disable hangcheck

    Tags: the following tags are taken into account when attached to the node:
        'serial', 'cramfs', 'kvariant', 'kargs', 'no-hangcheck'

    Security:
        - Non-admins can only generate files for nodes at their sites.
        - Non-admins, when they provide a filename, *must* specify it in the %d area

   Housekeeping:
        Whenever needed, the method stores intermediate files in a
        private area, typically not located under the web server's
        accessible area, and are cleaned up by the method.

    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        Parameter (str, "Action mode, expected value depends of the type of node"),
        Parameter (str, "Empty string for verbatim result, resulting file full path otherwise"),
        Parameter ([str], "Options"),
        ]

    returns = Parameter(str, "Node boot medium, either inlined, or filename, depending on the filename parameter")

    # define globals for regular nodes, override later for other types
    BOOTCDDIR = "/usr/share/bootcd-@NODEFAMILY@/"
    BOOTCDBUILD = "/usr/share/bootcd-@NODEFAMILY@/build.sh"
    GENERICDIR = "/var/www/html/download-@NODEFAMILY@/"
    WORKDIR = "/var/tmp/bootmedium"
    DEBUG = False
    # uncomment this to preserve temporary area and bootcustom logs
    #DEBUG = True

    ### returns (host, domain) :
    # 'host' : host part of the hostname
    # 'domain' : domain part of the hostname
    def split_hostname (self, node):
        # Split hostname into host and domain parts
        parts = node['hostname'].split(".", 1)
        if len(parts) < 2:
            raise PLCInvalidArgument, "Node hostname %s is invalid"%node['hostname']
        return parts

    # Generate the node (plnode.txt) configuration content.
    #
    # This function will create the configuration file a node
    # composed by:
    #  - a common part, regardless of the 'node_type' tag
    #  - XXX a special part, depending on the 'node_type' tag value.
    def floppy_contents (self, node, renew_key):

        # Do basic checks
        if node['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local node"

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to generate a configuration file for %s"%node['hostname']

        # Get interface for this node
        primary = None
        interfaces = Interfaces(self.api, node['interface_ids'])
        for interface in interfaces:
            if interface['is_primary']:
                primary = interface
                break
        if primary is None:
            raise PLCInvalidArgument, "No primary network configured on %s"%node['hostname']

        ( host, domain ) = self.split_hostname (node)

        # renew the key and save it on the database
        if renew_key:
            node['key'] = compute_key()
            node.update_last_download(commit=False)
            node.sync()

        # Generate node configuration file suitable for BootCD
        file = ""

        if renew_key:
            file += 'NODE_ID="%d"\n' % node['node_id']
            file += 'NODE_KEY="%s"\n' % node['key']
            # not used anywhere, just a note for operations people
            file += 'KEY_RENEWAL_DATE="%s"\n' % time.strftime('%Y/%m/%d at %H:%M +0000',time.gmtime())

        if primary['mac']:
            file += 'NET_DEVICE="%s"\n' % primary['mac'].lower()

        file += 'IP_METHOD="%s"\n' % primary['method']

        if primary['method'] == 'static':
            file += 'IP_ADDRESS="%s"\n' % primary['ip']
            file += 'IP_GATEWAY="%s"\n' % primary['gateway']
            file += 'IP_NETMASK="%s"\n' % primary['netmask']
            file += 'IP_NETADDR="%s"\n' % primary['network']
            file += 'IP_BROADCASTADDR="%s"\n' % primary['broadcast']
            file += 'IP_DNS1="%s"\n' % primary['dns1']
            file += 'IP_DNS2="%s"\n' % (primary['dns2'] or "")

        file += 'HOST_NAME="%s"\n' % host
        file += 'DOMAIN_NAME="%s"\n' % domain

        # define various interface settings attached to the primary interface
        settings = InterfaceTags (self.api, {'interface_id':interface['interface_id']})

        categories = set()
        for setting in settings:
            if setting['category'] is not None:
                categories.add(setting['category'])

        for category in categories:
            category_settings = InterfaceTags(self.api,{'interface_id':interface['interface_id'],
                                                              'category':category})
            if category_settings:
                file += '### Category : %s\n'%category
                for setting in category_settings:
                    file += '%s_%s="%s"\n'%(category.upper(),setting['tagname'].upper(),setting['value'])

        for interface in interfaces:
            if interface['method'] == 'ipmi':
                file += 'IPMI_ADDRESS="%s"\n' % interface['ip']
                if interface['mac']:
                    file += 'IPMI_MAC="%s"\n' % interface['mac'].lower()
                break

        return file

    # see also GetNodeFlavour that does similar things
    def get_nodefamily (self, node, auth):
        pldistro = self.api.config.PLC_FLAVOUR_NODE_PLDISTRO
        fcdistro = self.api.config.PLC_FLAVOUR_NODE_FCDISTRO
        arch = self.api.config.PLC_FLAVOUR_NODE_ARCH
        if not node:
            return (pldistro,fcdistro,arch)

        node_id=node['node_id']

        # no support for deployment-based BootCD's, use kvariants instead
        node_pldistro = GetNodePldistro (self.api,self.caller).call(auth, node_id)
        if node_pldistro: pldistro = node_pldistro

        node_fcdistro = GetNodeFcdistro (self.api,self.caller).call(auth, node_id)
        if node_fcdistro: fcdistro = node_fcdistro

        node_arch = GetNodeArch (self.api,self.caller).call(auth,node_id)
        if node_arch: arch = node_arch

        return (pldistro,fcdistro,arch)

    def bootcd_version (self):
        try:
            return file(self.BOOTCDDIR + "/build/version.txt").readline().strip()
        except:
            raise Exception,"Unknown boot cd version - probably wrong bootcd dir : %s"%self.BOOTCDDIR

    def cleantrash (self):
        for file in self.trash:
            if self.DEBUG:
                print 'DEBUG -- preserving',file
            else:
                os.unlink(file)

    ### handle filename
    # build the filename string
    # check for permissions and concurrency
    # returns the filename
    def handle_filename (self, filename, nodename, suffix, arch):
        # allow to set filename to None or any other empty value
        if not filename: filename=''
        filename = filename.replace ("%d",self.WORKDIR)
        filename = filename.replace ("%n",nodename)
        filename = filename.replace ("%s",suffix)
        filename = filename.replace ("%p",self.api.config.PLC_NAME)
        # let's be cautious
        try: filename = filename.replace ("%f", self.nodefamily)
        except: pass
        try: filename = filename.replace ("%a", arch)
        except: pass
        try: filename = filename.replace ("%v",self.bootcd_version())
        except: pass

        ### Check filename location
        if filename != '':
            if 'admin' not in self.caller['roles']:
                if ( filename.index(self.WORKDIR) != 0):
                    raise PLCInvalidArgument, "File %s not under %s"%(filename,self.WORKDIR)

            ### output should not exist (concurrent runs ..)
            # numerous reports of issues with this policy
            # looks like people sometime suspend/cancel their download
            # and this leads to the old file sitting in there forever
            # so, if the file is older than 5 minutes, we just trash
            grace=5
            if os.path.exists(filename) and (time.time()-os.path.getmtime(filename)) >= (grace*60):
                os.unlink(filename)
            if os.path.exists(filename):
                raise PLCInvalidArgument, "Resulting file %s already exists - please try again in %d minutes"%\
                    (filename,grace)

            ### we can now safely create the file,
            ### either we are admin or under a controlled location
            filedir=os.path.dirname(filename)
            # dirname does not return "." for a local filename like its shell counterpart
            if filedir:
                if not os.path.exists(filedir):
                    try:
                        os.makedirs (filedir,0777)
                    except:
                        raise PLCPermissionDenied, "Could not create dir %s"%filedir

        return filename

    # Build the command line to be executed
    # according the node type
    def build_command(self, node_type, build_sh_spec, node_image, type, floppy_file, log_file):

        command = ""

        # regular node, make build's arguments
        # and build the full command line to be called
        if node_type in [ 'regular', 'reservable' ]:

            build_sh_options=""
            if "cramfs" in build_sh_spec:
                type += "_cramfs"
            if "serial" in build_sh_spec:
                build_sh_options += " -s %s"%build_sh_spec['serial']
            if "variant" in build_sh_spec:
                build_sh_options += " -V %s"%build_sh_spec['variant']

            for karg in build_sh_spec['kargs']:
                build_sh_options += ' -k "%s"'%karg

            log_file="%s.log"%node_image

            command = '%s -f "%s" -o "%s" -t "%s" %s &> %s' % (self.BOOTCDBUILD,
                                                                 floppy_file,
                                                                 node_image,
                                                                 type,
                                                                 build_sh_options,
                                                                 log_file)

        if self.DEBUG:
            print "The build command line is %s" % command

        return command

    def call(self, auth, node_id_or_hostname, action, filename, options = []):

        self.trash=[]

        ### compute file suffix and type
        if action.find("-iso") >= 0 :
            suffix=".iso"
            type = "iso"
        elif action.find("-usb") >= 0:
            suffix=".usb"
            type = "usb"
        else:
            suffix=".txt"
            type = "txt"

        # check for node existence and get node_type
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id_or_hostname
        node = nodes[0]

        if self.DEBUG: print "%s required on node %s. Node type is: %s" \
                % (action, node['node_id'], node['node_type'])

        # check the required action against the node type
        node_type = node['node_type']
        if action not in allowed_actions[node_type]:
            raise PLCInvalidArgument, "Action %s not valid for %s nodes, valid actions are %s" \
                                   % (action, node_type, "|".join(allowed_actions[node_type]))

        # handle / canonicalize options
        if type == "txt":
            if options:
                raise PLCInvalidArgument, "Options are not supported for node configs"
        else:
            # create a dict for build.sh
            build_sh_spec={'kargs':[]}
            # use node tags as defaults
            # check for node tag equivalents
            tags = NodeTags(self.api,
                            {'node_id': node['node_id'],
                             'tagname': ['serial', 'cramfs', 'kvariant', 'kargs', 'no-hangcheck']},
                            ['tagname', 'value'])
            if tags:
                for tag in tags:
                    if tag['tagname'] == 'serial':
                        build_sh_spec['serial'] = tag['value']
                    if tag['tagname'] == 'cramfs':
                        build_sh_spec['cramfs'] = True
                    if tag['tagname'] == 'kvariant':
                        build_sh_spec['variant'] = tag['value']
                    if tag['tagname'] == 'kargs':
                        build_sh_spec['kargs'] += tag['value'].split()
                    if tag['tagname'] == 'no-hangcheck':
                        build_sh_spec['kargs'].append('hcheck_reboot0')
            # then options can override tags
            for option in options:
                if option == "cramfs":
                    build_sh_spec['cramfs']=True
                elif option == 'partition':
                    if type != "usb":
                        raise PLCInvalidArgument, "option 'partition' is for USB images only"
                    else:
                        type="usb_partition"
                elif option == "serial":
                    build_sh_spec['serial']='default'
                elif option.find("serial:") == 0:
                    build_sh_spec['serial']=option.replace("serial:","")
                elif option.find("variant:") == 0:
                    build_sh_spec['variant']=option.replace("variant:","")
                elif option == "no-hangcheck":
                    build_sh_spec['kargs'].append('hcheck_reboot0')
                else:
                    raise PLCInvalidArgument, "unknown option %s"%option

        # compute nodename according the action
        if action.find("node-") == 0:
            nodename = node['hostname']
        else:
            node = None
            # compute a 8 bytes random number
            tempbytes = random.sample (xrange(0,256), 8);
            def hexa2 (c): return chr((c>>4)+65) + chr ((c&16)+65)
            nodename = "".join(map(hexa2,tempbytes))

        # get nodefamily
        (pldistro,fcdistro,arch) = self.get_nodefamily(node,auth)
        self.nodefamily="%s-%s-%s"%(pldistro,fcdistro,arch)

        # apply on globals
        for attr in [ "BOOTCDDIR", "BOOTCDBUILD", "GENERICDIR" ]:
            setattr(self,attr,getattr(self,attr).replace("@NODEFAMILY@",self.nodefamily))

        filename = self.handle_filename(filename, nodename, suffix, arch)

        # log call
        if node:
            self.message='GetBootMedium on node %s - action=%s'%(nodename,action)
            self.event_objects={'Node': [ node ['node_id'] ]}
        else:
            self.message='GetBootMedium - generic - action=%s'%action

        ### generic media
        if action == 'generic-iso' or action == 'generic-usb':
            if options:
                raise PLCInvalidArgument, "Options are not supported for generic images"
            # this raises an exception if bootcd is missing
            version = self.bootcd_version()
            generic_name = "%s-BootCD-%s%s"%(self.api.config.PLC_NAME,
                                             version,
                                             suffix)
            generic_path = "%s/%s" % (self.GENERICDIR,generic_name)

            if filename:
                ret=os.system ('cp "%s" "%s"'%(generic_path,filename))
                if ret==0:
                    return filename
                else:
                    raise PLCPermissionDenied, "Could not copy %s into %s"%(generic_path,filename)
            else:
                ### return the generic medium content as-is, just base64 encoded
                return base64.b64encode(file(generic_path).read())

        ### config file preview or regenerated
        if action == 'node-preview' or action == 'node-floppy':
            renew_key = (action == 'node-floppy')
            floppy = self.floppy_contents (node,renew_key)
            if filename:
                try:
                    file(filename,'w').write(floppy)
                except:
                    raise PLCPermissionDenied, "Could not write into %s"%filename
                return filename
            else:
                return floppy

        ### we're left with node-iso and node-usb
        # the steps involved in the image creation are:
        # - create and test the working environment
        # - generate the configuration file
        # - build and invoke the build command
        # - delivery the resulting image file

        if action == 'node-iso' or action == 'node-usb':

            ### check we've got required material
            version = self.bootcd_version()

            if not os.path.isfile(self.BOOTCDBUILD):
                raise PLCAPIError, "Cannot locate bootcd/build.sh script %s"%self.BOOTCDBUILD

            # create the workdir if needed
            if not os.path.isdir(self.WORKDIR):
                try:
                    os.makedirs(self.WORKDIR,0777)
                    os.chmod(self.WORKDIR,0777)
                except:
                    raise PLCPermissionDenied, "Could not create dir %s"%self.WORKDIR

            try:
                # generate floppy config
                floppy_text = self.floppy_contents(node,True)
                # store it
                floppy_file = "%s/%s.txt"%(self.WORKDIR,nodename)
                try:
                    file(floppy_file,"w").write(floppy_text)
                except:
                    raise PLCPermissionDenied, "Could not write into %s"%floppy_file

                self.trash.append(floppy_file)

                node_image = "%s/%s%s"%(self.WORKDIR,nodename,suffix)
                log_file="%s.log"%node_image

                command = self.build_command(node_type, build_sh_spec, node_image, type, floppy_file, log_file)

                # invoke the image build script
                if command != "":
                    ret=os.system(command)

                if ret != 0:
                    raise PLCAPIError, "%s failed Command line was: %s Error logs: %s" % \
                              (self.BOOTCDBUILD,  command, file(log_file).read())

                self.trash.append(log_file)

                if not os.path.isfile (node_image):
                    raise PLCAPIError,"Unexpected location of build.sh output - %s"%node_image

                # handle result
                if filename:
                    ret=os.system('mv "%s" "%s"'%(node_image,filename))
                    if ret != 0:
                        self.trash.append(node_image)
                        self.cleantrash()
                        raise PLCAPIError, "Could not move node image %s into %s"%(node_image,filename)
                    self.cleantrash()
                    return filename
                else:
                    result = file(node_image).read()
                    self.trash.append(node_image)
                    self.cleantrash()
                    return base64.b64encode(result)
            except:
                self.cleantrash()
                raise

        # we're done here, or we missed something
        raise PLCAPIError,'Unhandled action %s'%action

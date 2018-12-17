# pylint: disable=c0111, c0103

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

from PLC.Logger import logger

from PLC.Accessors.Accessors_standard import *              # node accessors

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
    int8s = random.sample(range(0, 256), 32)
    # Base64 encode their string representation
    key = base64.b64encode(bytes(int8s))
    # Boot Manager cannot handle = in the key
    key = key.replace(b"=", b"")
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
        - 'systemd-debug' - turn on systemd debug in bootcd

    Tags: the following tags are taken into account when attached to the node:
        'serial', 'cramfs', 'kvariant', 'kargs', 'no-hangcheck', 'systemd-debug'

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
    LOGDIR = "/var/tmp/bootmedium/logs/"
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
            raise PLCInvalidArgument("Node hostname {} is invalid".format(node['hostname']))
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
            raise PLCInvalidArgument("Not a local node {}".format(node['hostname']))

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied(
                    "Not allowed to generate a configuration file for {}"\
                    .format(node['hostname']))

        # Get interface for this node
        primary = None
        interfaces = Interfaces(self.api, node['interface_ids'])
        for interface in interfaces:
            if interface['is_primary']:
                primary = interface
                break
        if primary is None:
            raise PLCInvalidArgument(
                "No primary network configured on {}".format(node['hostname']))

        host, domain = self.split_hostname (node)

        # renew the key and save it on the database
        if renew_key:
            node['key'] = compute_key()
            node.update_last_download(commit=False)
            node.sync()

        # Generate node configuration file suitable for BootCD
        file = ""

        if renew_key:
            file += 'NODE_ID="{}"\n'.format(node['node_id'])
            file += 'NODE_KEY="{}"\n'.format(node['key'])
            # not used anywhere, just a note for operations people
            file += 'KEY_RENEWAL_DATE="{}"\n'\
                .format(time.strftime('%Y/%m/%d at %H:%M +0000',time.gmtime()))

        if primary['mac']:
            file += 'NET_DEVICE="{}"\n'.format(primary['mac'].lower())

        file += 'IP_METHOD="{}"\n'.format(primary['method'])

        if primary['method'] == 'static':
            file += 'IP_ADDRESS="{}"\n'.format(primary['ip'])
            file += 'IP_GATEWAY="{}"\n'.format(primary['gateway'])
            file += 'IP_NETMASK="{}"\n'.format(primary['netmask'])
            file += 'IP_NETADDR="{}"\n'.format(primary['network'])
            file += 'IP_BROADCASTADDR="{}"\n'.format(primary['broadcast'])
            file += 'IP_DNS1="{}"\n'.format(primary['dns1'])
            file += 'IP_DNS2="{}"\n'.format(primary['dns2'] or "")

        file += 'HOST_NAME="{}"\n'.format(host)
        file += 'DOMAIN_NAME="{}"\n'.format(domain)

        # define various interface settings attached to the primary interface
        settings = InterfaceTags (self.api, {'interface_id':interface['interface_id']})

        categories = set()
        for setting in settings:
            if setting['category'] is not None:
                categories.add(setting['category'])

        for category in categories:
            category_settings = InterfaceTags(self.api,{'interface_id' : interface['interface_id'],
                                                        'category' : category})
            if category_settings:
                file += '### Category : {}\n'.format(category)
                for setting in category_settings:
                    file += '{}_{}="{}"\n'\
                        .format(category.upper(), setting['tagname'].upper(), setting['value'])

        for interface in interfaces:
            if interface['method'] == 'ipmi':
                file += 'IPMI_ADDRESS="{}"\n'.format(interface['ip'])
                if interface['mac']:
                    file += 'IPMI_MAC="{}"\n'.format(interface['mac'].lower())
                break

        return file

    # see also GetNodeFlavour that does similar things
    def get_nodefamily (self, node, auth):
        pldistro = self.api.config.PLC_FLAVOUR_NODE_PLDISTRO
        fcdistro = self.api.config.PLC_FLAVOUR_NODE_FCDISTRO
        arch = self.api.config.PLC_FLAVOUR_NODE_ARCH
        if not node:
            return (pldistro,fcdistro,arch)

        node_id = node['node_id']

        # no support for deployment-based BootCD's, use kvariants instead
        node_pldistro = GetNodePldistro (self.api,self.caller).call(auth, node_id)
        if node_pldistro:
            pldistro = node_pldistro

        node_fcdistro = GetNodeFcdistro (self.api,self.caller).call(auth, node_id)
        if node_fcdistro:
            fcdistro = node_fcdistro

        node_arch = GetNodeArch (self.api,self.caller).call(auth,node_id)
        if node_arch:
            arch = node_arch

        return (pldistro,fcdistro,arch)

    def bootcd_version (self):
        try:
            with open(self.BOOTCDDIR + "/build/version.txt") as feed:
                return feed.readline().strip()
        except:
            raise Exception("Unknown boot cd version - probably wrong bootcd dir : {}"\
                            .format(self.BOOTCDDIR))

    def cleantrash (self):
        for file in self.trash:
            if self.DEBUG:
                logger.debug('DEBUG -- preserving trash file {}'.format(file))
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
                    raise PLCInvalidArgument("File {} not under {}".format(filename, self.WORKDIR))

            ### output should not exist (concurrent runs ..)
            # numerous reports of issues with this policy
            # looks like people sometime suspend/cancel their download
            # and this leads to the old file sitting in there forever
            # so, if the file is older than 5 minutes, we just trash
            grace=5
            if os.path.exists(filename) and (time.time()-os.path.getmtime(filename)) >= (grace*60):
                os.unlink(filename)
            if os.path.exists(filename):
                raise PLCInvalidArgument(
                    "Resulting file {} already exists - please try again in {} minutes"\
                    .format(filename, grace))

            ### we can now safely create the file,
            ### either we are admin or under a controlled location
            filedir=os.path.dirname(filename)
            # dirname does not return "." for a local filename like its shell counterpart
            if filedir:
                if not os.path.exists(filedir):
                    try:
                        os.makedirs (filedir,0o777)
                    except:
                        raise PLCPermissionDenied("Could not create dir {}".format(filedir))

        return filename

    def build_command(self, nodename, node_type, build_sh_spec, node_image, type, floppy_file):
        """
        returns a tuple
        (*) build command to be run
        (*) location of the log_file
        """

        command = ""

        # regular node, make build's arguments
        # and build the full command line to be called
        if node_type not in [ 'regular', 'reservable' ]:
            logger.error("GetBootMedium.build_command: unexpected node_type {}".format(node_type))
            return command, None

        build_sh_options=""
        if "cramfs" in build_sh_spec:
            type += "_cramfs"
        if "serial" in build_sh_spec:
            build_sh_options += " -s {}".format(build_sh_spec['serial'])
        if "variant" in build_sh_spec:
            build_sh_options += " -V {}".format(build_sh_spec['variant'])

        for karg in build_sh_spec['kargs']:
            build_sh_options += ' -k "{}"'.format(karg)

        import time
        date = time.strftime('%Y-%m-%d-%H-%M', time.gmtime())
        if not os.path.isdir(self.LOGDIR):
            os.makedirs(self.LOGDIR)
        log_file = "{}/{}-{}.log".format(self.LOGDIR, date, nodename)

        command = '{} -f "{}" -o "{}" -t "{}" {} > {} 2>&1'\
                  .format(self.BOOTCDBUILD,
                          floppy_file,
                          node_image,
                          type,
                          build_sh_options,
                          log_file)

        logger.info("The build command line is {}".format(command))

        return command, log_file

    def call(self, auth, node_id_or_hostname, action, filename, options = []):

        self.trash=[]

        ### compute file suffix and type
        if action.find("-iso") >= 0 :
            suffix = ".iso"
            type   = "iso"
        elif action.find("-usb") >= 0:
            suffix = ".usb"
            type   = "usb"
        else:
            suffix = ".txt"
            type   = "txt"

        # check for node existence and get node_type
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument("No such node {}".format(node_id_or_hostname))
        node = nodes[0]

        logger.info("GetBootMedium: {} requested on node {}. Node type is: {}"\
            .format(action, node['node_id'], node['node_type']))

        # check the required action against the node type
        node_type = node['node_type']
        if action not in allowed_actions[node_type]:
            raise PLCInvalidArgument("Action {} not valid for {} nodes, valid actions are {}"\
                                   .format(action, node_type, "|".join(allowed_actions[node_type])))

        # handle / canonicalize options
        if type == "txt":
            if options:
                raise PLCInvalidArgument("Options are not supported for node configs")
        else:
            # create a dict for build.sh
            build_sh_spec={'kargs':[]}
            # use node tags as defaults
            # check for node tag equivalents
            tags = NodeTags(self.api,
                            {'node_id': node['node_id'],
                             'tagname': ['serial', 'cramfs', 'kvariant', 'kargs',
                                         'no-hangcheck', 'systemd-debug' ]},
                            ['tagname', 'value'])
            if tags:
                for tag in tags:
                    if tag['tagname'] == 'serial':
                        build_sh_spec['serial'] = tag['value']
                    elif tag['tagname'] == 'cramfs':
                        build_sh_spec['cramfs'] = True
                    elif tag['tagname'] == 'kvariant':
                        build_sh_spec['variant'] = tag['value']
                    elif tag['tagname'] == 'kargs':
                        build_sh_spec['kargs'] += tag['value'].split()
                    elif tag['tagname'] == 'no-hangcheck':
                        build_sh_spec['kargs'].append('hcheck_reboot0')
                    elif tag['tagname'] == 'systemd-debug':
                        build_sh_spec['kargs'].append('systemd.log_level=debug')
                        build_sh_spec['kargs'].append('systemd.log_target=console')
            # then options can override tags
            for option in options:
                if option == "cramfs":
                    build_sh_spec['cramfs']=True
                elif option == 'partition':
                    if type != "usb":
                        raise PLCInvalidArgument("option 'partition' is for USB images only")
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
                elif option == "systemd-debug":
                    build_sh_spec['kargs'].append('systemd.log_level=debug')
                else:
                    raise PLCInvalidArgument("unknown option {}".format(option))

        # compute nodename according the action
        if action.find("node-") == 0:
            nodename = node['hostname']
        else:
            node = None
            # compute a 8 bytes random number
            tempbytes = random.sample (range(0,256), 8);
            def hexa2 (c): return chr((c>>4)+65) + chr ((c&16)+65)
            nodename = "".join(map(hexa2,tempbytes))

        # get nodefamily
        (pldistro,fcdistro,arch) = self.get_nodefamily(node, auth)
        self.nodefamily="{}-{}-{}".format(pldistro, fcdistro, arch)

        # apply on globals
        for attr in [ "BOOTCDDIR", "BOOTCDBUILD", "GENERICDIR" ]:
            setattr(self,attr,getattr(self,attr).replace("@NODEFAMILY@",self.nodefamily))

        filename = self.handle_filename(filename, nodename, suffix, arch)

        # log call
        if node:
            self.message='GetBootMedium on node {} - action={}'.format(nodename, action)
            self.event_objects={'Node': [ node ['node_id'] ]}
        else:
            self.message='GetBootMedium - generic - action={}'.format(action)

        ### generic media
        if action == 'generic-iso' or action == 'generic-usb':
            if options:
                raise PLCInvalidArgument("Options are not supported for generic images")
            # this raises an exception if bootcd is missing
            version = self.bootcd_version()
            generic_name = "{}-BootCD-{}{}".format(self.api.config.PLC_NAME, version, suffix)
            generic_path = "{}/{}".format(self.GENERICDIR, generic_name)

            if filename:
                ret=os.system ('cp "{}" "{}"'.format(generic_path, filename))
                if ret==0:
                    return filename
                else:
                    raise PLCPermissionDenied("Could not copy {} into {}"\
                                              .format(generic_path, filename))
            else:
                ### return the generic medium content as-is, just base64 encoded
                with open(generic_path) as feed:
                    return base64.b64encode(feed.read())

        ### config file preview or regenerated
        if action == 'node-preview' or action == 'node-floppy':
            renew_key = (action == 'node-floppy')
            floppy = self.floppy_contents (node,renew_key)
            if filename:
                try:
                    with open(filename, 'w') as writer:
                        writer.write(floppy)
                except:
                    raise PLCPermissionDenied("Could not write into {}".format(filename))
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
                raise PLCAPIError("Cannot locate bootcd/build.sh script {}".format(self.BOOTCDBUILD))

            # create the workdir if needed
            if not os.path.isdir(self.WORKDIR):
                try:
                    os.makedirs(self.WORKDIR,0o777)
                    os.chmod(self.WORKDIR,0o777)
                except:
                    raise PLCPermissionDenied("Could not create dir {}".format(self.WORKDIR))

            try:
                # generate floppy config
                floppy_text = self.floppy_contents(node, True)
                # store it
                floppy_file = "{}/{}.txt".format(self.WORKDIR, nodename)
                try:
                    with open(floppy_file, "w") as writer:
                        writer.write(floppy_text)
                except:
                    raise PLCPermissionDenied("Could not write into {}".format(floppy_file))

                self.trash.append(floppy_file)

                node_image = "{}/{}{}".format(self.WORKDIR, nodename, suffix)

                command, log_file = self.build_command(nodename, node_type, build_sh_spec,
                                                       node_image, type, floppy_file)

                # invoke the image build script
                if command != "":
                    ret = os.system(command)

                if ret != 0:
                    raise PLCAPIError("{} failed Command line was: {} See logs in {}"\
                                      .format(self.BOOTCDBUILD, command, log_file))

                if not os.path.isfile(node_image):
                    raise PLCAPIError("Unexpected location of build.sh output - {}".format(node_image))

                # handle result
                if filename:
                    ret = os.system('mv "{}" "{}"'.format(node_image, filename))
                    if ret != 0:
                        self.trash.append(node_image)
                        self.cleantrash()
                        raise PLCAPIError("Could not move node image {} into {}"\
                                          .format(node_image, filename))
                    self.cleantrash()
                    return filename
                else:
                    with open(node_image, "rb") as feed:
                        result = feed.read()
                    self.trash.append(node_image)
                    self.cleantrash()
                    logger.info("GetBootMedium - done with build.sh")
                    encoded_result = base64.b64encode(result)
                    logger.info("GetBootMedium - done with base64 encoding - lengths: raw={} - b64={}"
                                .format(len(result), len(encoded_result)))
                    return encoded_result
            except:
                self.cleantrash()
                raise

        # we're done here, or we missed something
        raise PLCAPIError('Unhandled action {}'.format(action))

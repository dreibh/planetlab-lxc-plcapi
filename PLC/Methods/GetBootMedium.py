# $Id$
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
from PLC.InterfaceSettings import InterfaceSetting, InterfaceSettings
from PLC.NodeTags import NodeTags

# could not define this in the class..
boot_medium_actions = [ 'node-preview',
                        'node-floppy',
                        'node-iso',
                        'node-usb',
                        'generic-iso',
                        'generic-usb',
                        ]

# compute a new key
# xxx used by GetDummyBoxMedium
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

    As compared with its ancestor, this method provides a much more detailed
    detailed interface, that allows to
    (*) either just preview the node config file -- in which case 
        the node key is NOT recomputed, and NOT provided in the output
    (*) or regenerate the node config file for storage on a floppy 
        that is, exactly what the ancestor method used todo, 
        including renewing the node's key
    (*) or regenerate the config file and bundle it inside an ISO or USB image
    (*) or just provide the generic ISO or USB boot images 
        in which case of course the node_id_or_hostname parameter is not used

    action is expected among the following string constants
    (*) node-preview
    (*) node-floppy
    (*) node-iso
    (*) node-usb
    (*) generic-iso
    (*) generic-usb

    Apart for the preview mode, this method generates a new node key for the
    specified node, effectively invalidating any old boot medium.

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
        - 'no-hangcheck'
        console_spec (or 'default') is passed as-is to bootcd/build.sh
        it is expected to be a colon separated string denoting
        tty - baudrate - parity - bits
        e.g. ttyS0:115200:n:8

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
        Parameter (str, "Action mode, expected in " + "|".join(boot_medium_actions)),
        Parameter (str, "Empty string for verbatim result, resulting file full path otherwise"),
        Parameter ([str], "Options"),
        ]

    returns = Parameter(str, "Node boot medium, either inlined, or filename, depending on the filename parameter")

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
        
    # plnode.txt content
    def floppy_contents (self, node, renew_key):

        if node['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local node"

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to generate a configuration file for %s"%node['hostname']

        # Get node networks for this node
        primary = None
        interfaces = Interfaces(self.api, node['interface_ids'])
        for interface in interfaces:
            if interface['is_primary']:
                primary = interface
                break
        if primary is None:
            raise PLCInvalidArgument, "No primary network configured on %s"%node['hostname']

        ( host, domain ) = self.split_hostname (node)

        if renew_key:
            node['key'] = compute_key()
            # Save it
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
        settings = InterfaceSettings (self.api, {'interface_id':interface['interface_id']})

        categories = set()
        for setting in settings:
            if setting['category'] is not None:
                categories.add(setting['category'])
        
        for category in categories:
            category_settings = InterfaceSettings(self.api,{'interface_id':interface['interface_id'],
                                                              'category':category})
            if category_settings:
                file += '### Category : %s\n'%category
                for setting in category_settings:
                    file += '%s_%s="%s"\n'%(category.upper(),setting['name'].upper(),setting['value'])

        for interface in interfaces:
            if interface['method'] == 'ipmi':
                file += 'IPMI_ADDRESS="%s"\n' % interface['ip']
                if interface['mac']:
                    file += 'IPMI_MAC="%s"\n' % interface['mac'].lower()
                break

        return file

    # see also InstallBootstrapFS in bootmanager that does similar things
    def get_nodefamily (self, node):
        # get defaults from the myplc build
        try:
            (pldistro,arch) = file("/etc/planetlab/nodefamily").read().strip().split("-")
        except:
            (pldistro,arch) = ("planetlab","i386")
            
        # with no valid argument, return system-wide defaults
        if not node:
            return (pldistro,arch)

        node_id=node['node_id']
        # cannot use accessors in the API itself
        # the 'arch' tag type is assumed to exist, see db-config
        arch_tags = NodeTags (self.api, {'tagname':'arch','node_id':node_id},['tagvalue'])
        if arch_tags:
            arch=arch_tags[0]['tagvalue']
        # ditto
        pldistro_tags = NodeTags (self.api, {'tagname':'pldistro','node_id':node_id},['tagvalue'])
        if pldistro_tags:
            pldistro=pldistro_tags[0]['tagvalue']

        return (pldistro,arch)

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

    def call(self, auth, node_id_or_hostname, action, filename, options = []):

        self.trash=[]
        ### check action
        if action not in boot_medium_actions:
            raise PLCInvalidArgument, "Unknown action %s"%action

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

        # handle / caconicalize options
        if type == "txt":
            if options:
                raise PLCInvalidArgument, "Options are not supported for node configs"
        else:
            # create a dict for build.sh 
            build_sh_spec={'-k':[]}
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
                elif option == "no-hangcheck":
                    build_sh_spec['-k'].append('hcheck_reboot=0')
                else:
                    raise PLCInvalidArgument, "unknown option %s"%option

        ### check node if needed
        if action.find("node-") == 0:
            nodes = Nodes(self.api, [node_id_or_hostname])
            if not nodes:
                raise PLCInvalidArgument, "No such node %r"%node_id_or_hostname
            node = nodes[0]
            nodename = node['hostname']

        else:
            node = None
            # compute a 8 bytes random number
            tempbytes = random.sample (xrange(0,256), 8);
            def hexa2 (c): return chr((c>>4)+65) + chr ((c&16)+65)
            nodename = "".join(map(hexa2,tempbytes))

        # get nodefamily
        (pldistro,arch) = self.get_nodefamily(node)
        self.nodefamily="%s-%s"%(pldistro,arch)
        # apply on globals
        for attr in [ "BOOTCDDIR", "BOOTCDBUILD", "GENERICDIR" ]:
            setattr(self,attr,getattr(self,attr).replace("@NODEFAMILY@",self.nodefamily))
            
        ### handle filename
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
            if os.path.exists(filename):
                raise PLCInvalidArgument, "Resulting file %s already exists"%filename

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
                ret=os.system ("cp %s %s"%(generic_path,filename))
                if ret==0:
                    return filename
                else:
                    raise PLCPermissionDenied, "Could not copy %s into"%(generic_path,filename)
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

                # make build's arguments
                build_sh_options=""
                if "cramfs" in build_sh_spec: 
                    type += "_cramfs"
                if "serial" in build_sh_spec: 
                    build_sh_options += " -s %s"%build_sh_spec['serial']
                
                for k_option in build_sh_spec['-k']:
                    build_sh_options += " -k %s"%k_option

                log_file="%s.log"%node_image
                # invoke build.sh
                build_command = '%s -f "%s" -o "%s" -t "%s" %s &> %s' % (self.BOOTCDBUILD,
                                                                         floppy_file,
                                                                         node_image,
                                                                         type,
                                                                         build_sh_options,
                                                                         log_file)
                if self.DEBUG:
                    print 'build command:',build_command
                ret=os.system(build_command)
                if ret != 0:
                    raise PLCAPIError,"bootcd/build.sh failed\n%s\n%s"%(
                        build_command,file(log_file).read())

                self.trash.append(log_file)
                if not os.path.isfile (node_image):
                    raise PLCAPIError,"Unexpected location of build.sh output - %s"%node_image
            
                # handle result
                if filename:
                    ret=os.system("mv %s %s"%(node_image,filename))
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


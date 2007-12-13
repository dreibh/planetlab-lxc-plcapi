import random
import base64
import os
import os.path

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.NodeNetworkSettings import NodeNetworkSetting, NodeNetworkSettings

#
# xxx todo
# Thierry on june 5 2007
# 
# it turns out that having either apache (when invoked through xmlrpc)
# or root (when running plcsh directly) run this piece of code is
# problematic. In fact although we try to create intermediate dirs
# with mode 777, what happens is that root's umask in the plc chroot
# jail is set to 0022.
# 
# the bottom line is, depending on who (apache or root) runs this for
# the first time, we can access denied issued (when root comes first)
# so probably we'd better implement a scheme where files are stored
# directly under /var/tmp or something
# 
# in addition the sequels of a former run (e.g. with a non-empty
# filename) can prevent subsequent runs if the file is not properly
# cleaned up after use, which is generally the case if someone invokes
# this through plcsh and does not clean up
# so maybe a dedicated cleanup method could be useful just in case
# 

# could not define this in the class..
boot_medium_actions = [ 'node-preview',
                        'node-floppy',
                        'node-iso',
                        'node-usb',
                        'generic-iso',
                        'generic-usb',
                        ]

class GetBootMedium(Method):
    """
    This method is a redesign based on former, supposedly dedicated, 
    AdmGenerateNodeConfFile

    As compared with its ancestor, this method provides a much more detailed
    detailed interface, that allows to
    (*) either just preview the node config file (in which case 
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

    Non-admins can only generate files for nodes at their sites.

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
        With the file-based return mechanism, the method returns the full pathname 
        of the result file; it is the caller's responsability to remove 
        this file after use.

    Options: an optional array of keywords. Currently supported are
        - 'serial'
        - 'cramfs'

    Security:
        When the user's role is not admin, the provided directory *must* be under
        the %d area

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

    returns = Parameter(str, "Node boot medium, either inlined, or filename, depending to the filename parameter")

    BOOTCDDIR = "/usr/share/bootcd/"
    BOOTCDBUILD = "/usr/share/bootcd/build.sh"
    GENERICDIR = "/var/www/html/download/"
    NODEDIR = "/var/tmp/bootmedium/results"
    WORKDIR = "/var/tmp/bootmedium/work"
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
        nodenetworks = NodeNetworks(self.api, node['nodenetwork_ids'])
        for nodenetwork in nodenetworks:
            if nodenetwork['is_primary']:
                primary = nodenetwork
                break
        if primary is None:
            raise PLCInvalidArgument, "No primary network configured on %s"%node['hostname']

        ( host, domain ) = self.split_hostname (node)

        if renew_key:
            # Generate 32 random bytes
            bytes = random.sample(xrange(0, 256), 32)
            # Base64 encode their string representation
            node['key'] = base64.b64encode("".join(map(chr, bytes)))
            # XXX Boot Manager cannot handle = in the key
            node['key'] = node['key'].replace("=", "")
            # Save it
            node.sync()

        # Generate node configuration file suitable for BootCD
        file = ""

        if renew_key:
            file += 'NODE_ID="%d"\n' % node['node_id']
            file += 'NODE_KEY="%s"\n' % node['key']

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

        # define various nodenetwork settings attached to the primary nodenetwork
        settings = NodeNetworkSettings (self.api, {'nodenetwork_id':nodenetwork['nodenetwork_id']})

        categories = set()
        for setting in settings:
            if setting['category'] is not None:
                categories.add(setting['category'])
        
        for category in categories:
            category_settings = NodeNetworkSettings(self.api,{'nodenetwork_id':nodenetwork['nodenetwork_id'],
                                                              'category':category})
            if category_settings:
                file += '### Category : %s\n'%category
                for setting in category_settings:
                    file += '%s_%s="%s"\n'%(category.upper(),setting['name'].upper(),setting['value'])

        for nodenetwork in nodenetworks:
            if nodenetwork['method'] == 'ipmi':
                file += 'IPMI_ADDRESS="%s"\n' % nodenetwork['ip']
                if nodenetwork['mac']:
                    file += 'IPMI_MAC="%s"\n' % nodenetwork['mac'].lower()
                break

        return file

    def bootcd_version (self):
        try:
            f = open (self.BOOTCDDIR + "/build/version.txt")
            version=f.readline().strip()
        finally:
            f.close()
        return version

    def cleandir (self,tempdir):
        if not self.DEBUG:
            os.system("rm -rf %s"%tempdir)

    def call(self, auth, node_id_or_hostname, action, filename, options = []):

        ### check action
        if action not in boot_medium_actions:
            raise PLCInvalidArgument, "Unknown action %s"%action

        ### compute file suffix and type
        if action.find("-iso") >= 0 :
            suffix=".iso"
            type = ["iso"]
        elif action.find("-usb") >= 0:
            suffix=".usb"
            type = ["usb"]
        else:
            suffix=".txt"
            type = ["txt"]

        if type != "txt":
            if 'serial' in options:
                suffix = "-serial" + suffix
                type.insert(1, "serial")
            if 'cramfs' in options:
                suffix = "-cramfs" + suffix
                # XXX must be the same index as above
                type.insert(1, "cramfs")
        type = "_".join(type)

        ### compute a 8 bytes random number
        tempbytes = random.sample (xrange(0,256), 8);
        def hexa2 (c):
            return chr((c>>4)+65) + chr ((c&16)+65)
        temp = "".join(map(hexa2,tempbytes))

        ### check node if needed
        if action.find("node-") == 0:
            nodes = Nodes(self.api, [node_id_or_hostname])
            if not nodes:
                raise PLCInvalidArgument, "No such node %r"%node_id_or_hostname
            node = nodes[0]
            nodename = node['hostname']
            
        else:
            node = None
            nodename = temp
            
        ### handle filename
        filename = filename.replace ("%d",self.NODEDIR)
        filename = filename.replace ("%n",nodename)
        filename = filename.replace ("%s",suffix)
        filename = filename.replace ("%p",self.api.config.PLC_NAME)
        # only if filename contains "%v", bootcd is maybe not avail ?
        if filename.find("%v") >=0:
            filename = filename.replace ("%v",self.bootcd_version())

        ### Check filename location
        if filename != '':
            if 'admin' not in self.caller['roles']:
                if ( filename.index(self.NODEDIR) != 0):
                    raise PLCInvalidArgument, "File %s not under %s"%(filename,self.NODEDIR)

            ### output should not exist (concurrent runs ..)
            if os.path.exists(filename):
                raise PLCInvalidArgument, "Resulting file %s already exists"%filename

            ### we can now safely create the file, 
            ### either we are admin or under a controlled location
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs (os.path.dirname(filename),0777)
                except:
                    raise PLCPermissionDenied, "Could not create dir %s"%os.path.dirname(filename)

        
        ### generic media
        if action == 'generic-iso' or action == 'generic-usb':
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

        ### floppy preview
        if action == 'node-preview':
            floppy = self.floppy_contents (node,False)
            if filename:
                try:
                    file(filename,'w').write(floppy)
                except:
                    raise PLCPermissionDenied, "Could not write into %s"%filename
                return filename
            else:
                return floppy

        if action == 'node-floppy':
            floppy = self.floppy_contents (node,True)
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

            # need a temporary area
            tempdir = "%s/%s"%(self.WORKDIR,nodename)
            if not os.path.isdir(tempdir):
                try:
                    os.makedirs(tempdir,0777)
                except:
                    raise PLCPermissionDenied, "Could not create dir %s"%tempdir
            
            try:
                # generate floppy config
                floppy = self.floppy_contents(node,True)
                # store it
                node_floppy = "%s/%s"%(tempdir,nodename)
                try:
                    file(node_floppy,"w").write(floppy)
                except:
                    raise PLCPermissionDenied, "Could not write into %s"%node_floppy

                node_image = "%s/%s"%(tempdir,nodename)
                # invoke build.sh
                build_command = '%s -f "%s" -O "%s" -t "%s" &> %s.log' % (self.BOOTCDBUILD,
                                                                          node_floppy,
                                                                          node_image,
                                                                          type,
                                                                          node_image)
                if self.DEBUG:
                    print 'build command:',build_command
                ret=os.system(build_command)
                if ret != 0:
                    raise PLCPermissionDenied,"build.sh failed to create node-specific medium"

                node_image += suffix
                if not os.path.isfile (node_image):
                    raise PLCAPIError,"Unexpected location of build.sh output - %s"%node_image
            
                # cache result
                if filename:
                    ret=os.system("mv %s %s"%(node_image,filename))
                    if ret != 0:
                        raise PLCAPIError, "Could not move node image %s into %s"%(node_image,filename)
                    self.cleandir(tempdir)
                    return filename
                else:
                    result = file(node_image).read()
                    self.cleandir(tempdir)
                    return base64.b64encode(result)
            except:
                self.cleandir(tempdir)
                raise
                
        # we're done here, or we missed something
        raise PLCAPIError,'Unhandled action %s'%action


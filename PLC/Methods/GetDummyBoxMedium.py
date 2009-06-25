#
# Marta Carbone - UniPi
# $Id$
#
# This class requires the rpm package containing
# the picobsd image to be installed
# on the Central Site system.
#

import base64
import os
import datetime

from PLC.Faults import *                          # faults library
from PLC.Method import Method                     # base class for methods
from PLC.Parameter import Parameter               # use the Parameter wrapper
from PLC.Auth import Auth                         # import the Auth parameter
from PLC.Nodes import *                           # nodes functions
from PLC.Methods.GetBootMedium import compute_key # key generation function
from PLC.Accessors.Accessors_dummynetbox import * # import dummynet accessors

WORK_DIR = "/var/tmp/DummynetBoxMedium"
BASE_IMAGE = "/usr/share/dummynet/picobsd"

class GetDummyBoxMedium(Method):
    """
    This method is used to fetch a boot image for the DummyNetBox
    with its configuration file embedded.

    Every time this method is called, a new key is generated in the configuration file,
    SO THIS OPERATION WILL INVALIDATE ANY PREVIOUSLY DUMMYNETBOX BOOT MEDIUM.

    This method updates the key fields in the database.
    It returns a base64-encoded boot image.
    """
    # I added the session role, because this method should be called from the web
    roles = ['admin', 'pi', 'tech', 'session']

    accepts = [
        Auth(),
        Parameter(int, "The dummybox_id"),
        Parameter(str, "The image type (bin or iso)")
    ]

    returns = Parameter(str, "DummynetBox boot medium")

    # XXX add checks for picobsd.bin existence

    # Generate a new configuration file in the working directory
    # input parameters follows:
    # self is used to access instance data,
    # dummybox is the dummybox_id,
    # new_key is the new generated key,
    # configfile is the output file of the configuration.
    def generate_conf_file(self, dummybox, new_key, configfile):
	
        # Generate the dummynet box configuration file
        today = datetime.date.today()
        file = ""
        file += "# This is the dummynetbox configuration file\n"
        file += "# and was generated on %s\n" % str(today)
        
        host_domain = dummybox['hostname']
        host_domain = host_domain.split('.', 1)
        file += 'HOST_NAME="%s"\n' % host_domain[0]
        file += 'DOMAIN_NAME="%s"\n' % host_domain[1]
        
        file += 'IP_ADDRESS="%s"\n' % dummybox['ip']
        file += 'IP_NETMASK="%s"\n' % dummybox['netmask']
        file += 'IP_GATEWAY="%s"\n' % dummybox['gateway']
        file += 'IP_DNS1="%s"\n' % dummybox['dns1']
        file += 'IP_DNS2="%s"\n' % dummybox['dns2']
        file += 'DUMMYBOX_ID="%s"\n' % dummybox['node_id']
        file += 'DUMMYBOX_KEY="%s"\n' % new_key
        
        file += 'CS_IP="%s"\n' % self.api.config.PLC_API_HOST

        # write the configuration file
        # WORK_DIR must be writable
        FILE = open(configfile, "w")
        FILE.write(file)
        FILE.close()
        
        return
        
    # Here starts the execution of the call
    def call(self, auth, dummybox_id, type):

        # check for dummynet box existence and get dummyboxes information
        dummybox_info = Nodes(self.api, {'node_id':dummybox_id, 'node_type':'dummynet'}, \
                ['hostname', 'interface_ids'])
 
        if dummybox_id != None and not dummybox_info:
            raise PLCInvalidArgument, "No such DummyBox %s" % dummybox_id

        # Get the dummynet box hostname
        dummybox_hostname = dummybox_info[0]['hostname']
	print "dummybox hostname %s" % dummybox_hostname

        # get the node interface, if configured
        interfaces = Interfaces(self.api, dummybox_info[0]['interface_ids'])
        for i in interfaces:
            if i['is_primary']:
                interface_info = i
                break

        if not interface_info:
            raise PLCInvalidArgument, "No primary network configured on %s" % dummybox_hostname

	dummybox = interface_info
        dummybox['hostname']=dummybox_hostname

	# Select the base image, default to bin image
        if type != 'iso':
                type="bin"
        IMAGE_NAME = str(WORK_DIR) + "/dummybox_" + dummybox_hostname + str(type)
        BASE_IMAGE = "/usr/share/dummynet/picobsd." + str(type)
        configfile = WORK_DIR + '/dummybox.conf'
        lockfile =  WORK_DIR + '/lockfile'

        # Permission checks
        assert self.caller is not None

        # Start the generation of the image
        # Generate a new key
        new_key = compute_key()

        # create working dir and lock file for concurrent runs
        if not os.path.exists(WORK_DIR):
            print "Creating working directory %s" % WORK_DIR
            os.mkdir(WORK_DIR)

        if os.path.exists(lockfile):
            raise PLCInvalidArgument, "Lockfile %s exist, try again " % lockfile
        else:
            print "Executing "+"touch %s" % lockfile
            os.system("touch %s" % lockfile)

        # generate the configuration file
        conf_file = self.generate_conf_file(dummybox, new_key, configfile)

        # build the shell script to customize the dummynetbox image
        # copy the raw file and find the configuration file position
        shell_script = "(cp %s %s; export MATCH=`grep -abo START_USER_DATA %s | cut -d: -f1`; " \
                           % (BASE_IMAGE, IMAGE_NAME, IMAGE_NAME)

	# set permission file
	shell_script += " chmod u+w %s; chmod u+w %s; " % (IMAGE_NAME, configfile)

        # cat the configuration file in the raw image
        shell_script += " cat %s | dd of=%s seek=$MATCH conv=notrunc bs=1)" \
                           % (configfile, IMAGE_NAME)

        # check returned values, 0 means OK, remove the lock file
        os.system(shell_script)
        os.system("rm %s" % (lockfile))

        # if all goes fine store the key in the database
        nodes = Nodes(self.api, dummybox_id)
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id_or_hostname
        nodes[0]['key'] = new_key
        nodes.sync()

        # return the file's content base64-encoded
        result = file(IMAGE_NAME).read()
        os.unlink(IMAGE_NAME)
        return base64.b64encode(result)
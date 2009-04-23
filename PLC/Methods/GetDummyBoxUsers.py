#
# Marta Carbone - UniPi 
# $Id$
#
# This Method returns a list of tuples formatted as follow:
# 
#      <key_id> <node_ip> <slicename>
#
# and an authorized_keys file, to be used on a dummynet box.
#

from PLC.Method import Method                   # base class used to derive methods
from PLC.Parameter import Parameter, Mixed      # define input parameters
from PLC.Auth import Auth                       # import the Auth parameter
from PLC.Faults import *                        # faults library
from PLC.Nodes import Node, Nodes               # main class for Nodes
from PLC.Slices import Slice, Slices            # main class for Slices
from PLC.Keys import Key, Keys                  # main class for Keys
from PLC.Persons import Person, Persons         # main class for Persons
from PLC.Interfaces import *			# get the node primary ip address
from PLC.NodeTags import *			# get node connected to a dummynet box
from PLC.Accessors.Accessors_dummynetbox import *                       # import dummynet accessors

# authorized file delimiter string
NEWFILE_MARK = "authorized_keys_mark"

# Dummynet box private key
KEY="/usr/share/dummynet/dbox_key"

class GetDummyBoxUsers(Method):
	"""
	Return a list of information about
	slice, users, user keys, nodes and dummyboxes.

	This Methods is mean to be used by a DummyBox.

	Return keys, 0 if there are no users.
	"""

	roles = ['admin', 'pi', 'node']

	accepts = [
		Auth(),
		Parameter(int, 'DummyBox id'),
	]

	returns = Parameter(str, "DummyBox files")

	def call(self, auth, dummybox_id = None):
		"""
		Get information about users on nodes connected to the DummyBox.

		Given a dummybox_id we get the list of connected nodes
		For each node_id we get a list of connected slices
		For each slice we get a list of connected users
		For each user we get a list of keys that we return to the caller.
		"""

		# These variables contain some text to be used
		# to format the output files
		# port-forwarding should be denied in the main sshd configuration file
		ssh_command = "/home/user/dbox.cmd "
		ssh_configuration = ",no-port-forwarding,no-agent-forwarding,no-X11-forwarding "

		# check for dummynet box existence and get dummyboxes information
		dummyboxes = Nodes(self.api, {'node_id':dummybox_id, 'node_type':'dummynet'}, ['site_id'])

		if dummybox_id != None and not dummyboxes:
			raise PLCInvalidArgument, "No such DummyBox %s" % dummybox_id

		dummybox = dummyboxes[0]

		# this method needs authentication
		assert self.caller is not None

		# XXX check if we have rights to do this operation:
		#  - admins can retrive all information they want,
		#  - dummyboxes can retrive information regarding their site,
		#    nodes and slice account present on their nodes.

		# Given a dummybox_id we get the list of connected nodes
		connected_nodes = NodeTags(self.api, {'value': dummybox_id}, ['node_id'])

		node_list = []
		for i in connected_nodes:
			node_list.append(i['node_id'])

		nodes = Nodes(self.api, node_list, ['node_id', 'hostname', 'slice_ids'])
		if not nodes: return 0

		# Here nodes should be an array of dict with 'node_id', 'hostname' and 'slice_ids' fields

		user_map = "# Permission file, check here if a user can configure a link\n" # store slice-node information
		user_map+= "# Tuples are `owner slice_name' `hostname to reconfigure'\n"
		authorized_keys_dict = {}	# user's keys, dictionary
		dbox_key_id = 0			# key_id used to identify users keys in the dummynetbox

		# For each node_id we get a list of connected slices
		for node in nodes:

			# list of connected slices
			slice_ids = node['slice_ids']
			if not slice_ids: continue

			# For each slice we get a list of connected users
			for slice_id in slice_ids:
				# field to return
				slice_name = Slices(self.api, {'slice_id': slice_id}, ['name', 'person_ids'])
				if not slice_name: continue

				# Given a slice we get a list of users 
				person_ids = slice_name[0]['person_ids']	
				if not person_ids: continue

				# For each user we get a list of keys
				for person_id in person_ids:
					# Given a user we get a list of keys
					person_list = Persons(self.api, {'person_id': person_id}, ['person_id','key_ids'])
					person = person_list[0]['person_id']
					key_list = person_list[0]['key_ids']
					if not key_list: continue

					for key_id in key_list:
						key = Keys(self.api, {'key_id': key_id}, ['key'])

						# Here we have all information we need
						# to build the authorized key file and
						# the user map file

						k = key[0]['key']

						# split the key in type/ssh_key/comment
						splitted_key = k.split(' ',2)
						uniq_key = splitted_key[0]+" "+splitted_key[1]

						# retrieve/create a unique dbox_key_id for this ssh_key
						if authorized_keys_dict.has_key(uniq_key):
							dbox_key_id = authorized_keys_dict[uniq_key]
						else:
							dbox_key_id+=1
							authorized_keys_dict.update({uniq_key : dbox_key_id})

						# get the node ip address
						nodenetworks = Interfaces(self.api, \
							{'node_id':node['node_id'], 'is_primary':'t'}, ['ip'])

						# append user and slice data to the user_map file	
						item = str(dbox_key_id)
						item +=" " + str(nodenetworks[0]['ip'])
						item +=" " + str(slice_name[0]['name']) + "\n"

						user_map += item

		# format change for authorized_keys dict
		authorized_keys_file=""	
		authorized_keys_file += "# generated automatically by GetUsersUpdate.py on the Central Site\n";
		authorized_keys_file += "# format file:\n";
		authorized_keys_file += '# command="command key_id $SSH_ORIGINAL_COMMAND",ssh_options key_type key comment\n'
		authorized_keys_file += "# where command, key_id and ssh_options are filled by the Central Site script\n"
		authorized_keys_file += "# and $SSH_ORIGINAL_COMMAND is the command line inserted by the node\n"
		authorized_keys_file += "\n";

		# read the central site key
		# the dummynet public key is located under KEY 
		try:
			pub_key=KEY+".pub"
			dbox_key_file = open(pub_key, 'r')
			dbox_key = dbox_key_file.readline()

			# upload the central site public key, used to
			# send plcapi commands to the central site
			# we use the special key_index = 0 value
			authorized_keys_file += "# The Central Site key, it allows to jump some checks on the dbox\n"
			authorized_keys_file += "command=\"" + ssh_command + "0";
			authorized_keys_file += " $SSH_ORIGINAL_COMMAND\"" + ssh_configuration + dbox_key + "\n"
			dbox_key_file.close()
		except:
			authorized_keys_file += "# The Central Site public key not found, this dummynet box\n";
			authorized_keys_file += "# will not accept configuration request coming from the Central Site\n";

		authorized_keys_file += "\n";
		# upload the users keys
		for i in authorized_keys_dict:
			# index of the key
			key_index = str(authorized_keys_dict[i])

			# create the dummynet box command
			authorized_keys_file += "command=\"" + ssh_command + key_index;
			authorized_keys_file += " $SSH_ORIGINAL_COMMAND\"" + ssh_configuration + str(i) + "\n"

		return user_map+NEWFILE_MARK+"\n"+authorized_keys_file

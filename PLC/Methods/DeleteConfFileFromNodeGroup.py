from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import Auth

class DeleteConfFileFromNodeGroup(Method):
    """
    Deletes a configuration file from the specified nodegroup. If the nodegroup
    is not linked to the configuration file, no errors are returned.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        ConfFile.fields['conf_file_id'],
        Mixed(NodeGroup.fields['nodegroup_id'],
              NodeGroup.fields['groupname'])
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, conf_file_id, nodegroup_id_or_name):
        # Get configuration file
        conf_files = ConfFiles(self.api, [conf_file_id])
        if not conf_files:
            raise PLCInvalidArgument, "No such configuration file"
        conf_file = conf_files[0]

        # Get nodegroup
        nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
        if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"
        nodegroup = nodegroups[0]

        # Link configuration file to nodegroup
        if nodegroup['nodegroup_id'] in conf_file['nodegroup_ids']:
            conf_file.remove_nodegroup(nodegroup)

        # Log affected objects
        self.event_objects = {'ConfFile': [conf_file_id],
                              'NodeGroup': [nodegroup['nodegroup_id']]}

        return 1

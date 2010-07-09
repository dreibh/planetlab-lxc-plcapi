# Baris Metin <tmetin@sophia.inria.fr>

import os
import xmlrpclib

from PLC.Slices import Slices
from PLC.SliceTags import SliceTags, SliceTag
from PLC.TagTypes import TagTypes
from PLC.Nodes import Nodes
from PLC.Config import Config
from pyaspects.meta import MetaAspect


class BaseOMF(object):

    def __init__(self):
        self.config = Config("/etc/planetlab/plc_config")
        self.slice = None

        # this was only for debugging, no need to log all method calls here -baris
        # self.log = open("/var/log/omf/plc_slice_calls.log", "a")
        self.log = None
        

    def logit(self, call, args, kwargs, data, slice):
        if not self.log: return

        self.log.write("%s : args: %s  kwargs: %s\n" % (call, args, kwargs))
        self.log.write("data: %s\n" % data)
        self.log.write("%s\n\n" % slice)
        self.log.flush()

           
    def get_slice(self, api, id_or_name):
        slice_filter = {}
        try: # if integer
            slice_filter['slice_id'] = int(str(id_or_name))
        except ValueError:
            # we have a string
            slice_filter['name'] = id_or_name
        slice = Slices(api, slice_filter = slice_filter)[0]
# don't bother to check for slice tags for the moment. we'll only
# create XMPP pubsub groups for all slices
#
#         slice_tags = SliceTags(api, slice_tag_filter = { 'slice_id': slice['slice_id'] })
#         omf_tag = [tag for tag in slice_tags if tag['name'] == 'omf']
#         if omf_tag and omf_tag['value'] not in ('false','0','no'):
#             # OK, slice has the "omf" tag set.
#             return slice
#         return None
        return slice

    def get_node_hostname(self, api, node_id_or_hostname):
        node_filter = {}
        try:
            node_filter['node_id'] = int(str(node_id_or_hostname))
        except ValueError:
            # we have a hostname
            node_filter['hostname'] = node_id_or_hostname

        try:
            node = Nodes(api, node_filter = node_filter)[0]
            return node['hostname']
        except IndexError:
            return None
        
    def get_slice_tags(self, api, slice_id):
        return SliceTags(api, slice_tag_filter = {'slice_id': slice_id})

    def get_tag_type(self, api, tagname):
        try:
            tag = TagTypes(api, {'tagname':tagname})[0]
            return tag
        except IndexError:
            return None

    def create_slice(self, slice):
        pass

    def add_resource(self, slice, resource):
        pass

    def delete_slice(self, slice):
        pass

    def delete_resource(self, slice, resource):
        pass

    # aspect method
    def before(self, wobj, data, *args, **kwargs):
        api_method_name = wobj.name
        slice_name_or_id = None
        node_ids = None

        if api_method_name == "AddSlice":
            slice_name_or_id = args[1]['name']
        elif api_method_name == "AddSliceToNodes" or api_method_name == "DeleteSliceFromNodes":
            slice_name_or_id = args[1]
            node_ids = args[2]
        elif api_method_name == "AddSliceTag":
            slice_name_or_id = args[1]
        elif api_method_name == "DeleteSlice":
            slice_name_or_id = args[1]        
        else: # ignore the rest
            #self.logit(wobj.name, args, kwargs, data, "SLICE")
            self.slice = None
            return

        self.slice = self.get_slice(wobj.api, slice_name_or_id)

        self.logit(wobj.name, args, kwargs, data, slice)

    # aspect method
    def after(self, wobj, data, *args, **kwargs):
        if not self.slice:
            return

        if data.has_key("method_return_value") and data['method_return_value'] == 1:
            # return value 1 means that API call was successful, we can go on.
            pass
        else:
            return

        api_method_name = wobj.name

        if api_method_name == "AddSlice":
            self.create_slice(slice['name'])
        elif api_method_name == "AddSliceToNodes":
            for node_id in node_ids:
                node_hostname = self.get_node_hostname(wobj.api, node_id)
                self.add_resource(slice['name'], node_hostname)
        elif api_method_name == "DeleteSlice":
            self.delete_slice(slice['name'])
        elif api_method_name == "DeleteSliceFromNodes":
            for node_id in node_ids:
                node_hostname = self.get_node_hostname(wobj.api, node_id)
                self.delete_resource(slice['name'], node_hostname)
        elif api_method_name == "AddSliceTag":
            # OMF slices need to have dotsshmount vsys tag set to be
            # able to access users' public keys.
            tag_type_id_or_name = args[2]
            omf_tag = self.get_tag_type(wobj.api, "omf_control")
            vsys_tag = self.get_tag_type(wobj.api, "vsys")
            if tag_type_id_or_name in (omf_tag['tagname'], omf_tag['tag_type_id']):
                slice_tag = SliceTag(wobj.api)
                slice_tag['slice_id'] = slice['slice_id']
                slice_tag['tag_type_id'] = vsys_tag['tag_type_id']
                slice_tag['value'] = u'dotsshmount'
                slice_tag.sync()

        self.logit(wobj.name, args, kwargs, data, slice)



class OMFAspect_xmlrpc(BaseOMF):
    __metaclass__ = MetaAspect
    name = "omfaspect_xmlrpc"

    def __init__(self):
        BaseOMF.__init__(self)

        slicemgr_url = self.config.PLC_OMF_SLICEMGR_URL
        self.server = xmlrpclib.ServerProxy(slicemgr_url, allow_none = 1)

    def create_slice(self, slice):
        self.server.createSlice(slice)

    def add_resource(self, slice, resource):
        self.server.addResource(slice, resource)

    def delete_slice(self, slice):
        self.server.deleteSlice(slice)
        
    def delete_resource(self, slice, resource):
        self.server.removeResource(slice, resource)

    def before(self, wobj, data, *args, **kwargs):
        BaseOMF.before(self, wobj, data, *args, **kwargs)

    def after(self, wobj, data, *args, **kwargs):
        BaseOMF.after(self, wobj, data, *args, **kwargs)



OMFAspect = OMFAspect_xmlrpc


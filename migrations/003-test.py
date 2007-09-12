#!/usr/bin/env plcsh

nnst = GetNodeNetworkSettingTypes(['interface_name'])
if nnst:
    print 'NodeNetworkSettingType interface_name already defined'
else:
    AddNodeNetworkSettingType({
        'category':'general',
        'min_role_id':30,
        'name':'interface_name',
        'description':'allows to specify a custom interface name'
        })
nnst_ifname_id = GetNodeNetworkSettingTypes(['interface_name'])[0]['nodenetwork_setting_type_id']


nnst = GetNodeNetworkSettingTypes(['ssid'])
if nnst:
    print 'NodeNetworkSettingType ssid already defined'
else:
    AddNodeNetworkSettingType({
        'category':'wifi',
        'min_role_id':30,
        'name':'ssid',
        'description':'allows to set ESSID'
        })
nnst_ssid_id = GetNodeNetworkSettingTypes(['ssid'])[0]['nodenetwork_setting_type_id']

nodename = 'onelab2.inria.fr'

nodenetwork_id=GetNodes(nodename)[0]['nodenetwork_ids'][0]

#######
nns_ifname = GetNodeNetworkSettings ({'nodenetwork_id':nodenetwork_id,
                                      'nodenetwork_setting_type_id':nnst_ifname_id})
if nns_ifname:
    print "interface name for %s already set (got %s - cat=%s)" %\
      (nodename,nns_ifname[0]['value'],nns_ifname[0]['category'])
else:
    AddNodeNetworkSetting(nodenetwork_id, 'interface_name', 'custom-eth0')
    
nns_ifname_id = GetNodeNetworkSettings ({'nodenetwork_id':nodenetwork_id,
                                         'nodenetwork_setting_type_id':nnst_ifname_id})[0]['nodenetwork_setting_id']
#######
nns_ssid = GetNodeNetworkSettings ({'nodenetwork_id':nodenetwork_id,
                                    'nodenetwork_setting_type_id':nnst_ssid_id})
if nns_ssid:
    print "ssid for %s already set (got %s - cat=%s)" %\
      (nodename,nns_ifname[0]['value'],nns_ifname[0]['category'])
else:
    AddNodeNetworkSetting(nodenetwork_id, 'ssid', 'init-onelab-g')
    
nns_ssid_id = GetNodeNetworkSettings ({'nodenetwork_id':nodenetwork_id,
                                       'nodenetwork_setting_type_id':nnst_ssid_id})[0]['nodenetwork_setting_id']

#######

UpdateNodeNetworkSetting (nns_ssid_id,'onelab-g')

DeleteNodeNetworkSetting (nns_ifname_id)


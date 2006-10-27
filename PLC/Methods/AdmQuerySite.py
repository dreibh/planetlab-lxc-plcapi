import socket

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks, valid_ip
from PLC.Auth import Auth

class AdmQuerySite(Method):
    """
    Deprecated. Functionality can be implemented with GetSites and
    GetNodes.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        {'site_name': Site.fields['name'],
         'site_abbreviatedname': Site.fields['abbreviated_name'],
         'site_loginbase': Site.fields['login_base'],
         'node_hostname': Node.fields['hostname'],
         'node_id': Node.fields['node_id'],
         'nodenetwork_ip': NodeNetwork.fields['ip'],
         'nodenetwork_mac': NodeNetwork.fields['mac']}
        ]

    returns = [Site.fields['site_id']]

    def call(self, auth, search_vals):
        if 'site_loginbase' in search_vals:
            sites = Sites(self.api, [search_vals['site_loginbase']]).values()
        else:
            sites = Sites(self.api).values()
            
        if 'site_name' in search_vals:
            sites = filter(lambda site: \
                           site['name'] == search_vals['site_name'],
                           sites)

        if 'site_abbreviatedname' in search_vals:
            sites = filter(lambda site: \
                           site['abbreviatedname'] == search_vals['site_abbreviatedname'],
                           sites)

        if 'node_id' in search_vals:
            sites = filter(lambda site: \
                           search_vals['node_id'] in site['node_ids'],
                           sites)

        if 'node_hostname' in search_vals or \
           'nodenetwork_ip' in search_vals or \
           'nodenetwork_mac' in search_vals:
            for site in sites:
                site['hostnames'] = []
                site['ips'] = []
                site['macs'] = []
                if site['node_ids']:
                    nodes = Nodes(self.api, site['node_ids']).values()
                    for node in nodes:
                        site['hostnames'].append(node['hostname'])
                        if 'nodenetwork_ip' in search_vals or \
                           'nodenetwork_mac' in search_vals:
                            nodenetworks = NodeNetworks(self.api, node['nodenetwork_ids']).values()
                            site['ips'] += [nodenetwork['ip'] for nodenetwork in nodenetworks]
                            site['macs'] += [nodenetwork['mac'] for nodenetwork in nodenetworks]

            if 'node_hostname' in search_vals:
                sites = filter(lambda site: \
                               search_vals['node_hostname'] in site['hostnames'],
                               sites)

            if 'nodenetwork_ip' in search_vals:
                sites = filter(lambda site: \
                               search_vals['nodenetwork_ip'] in site['ips'],
                               sites)

            if 'nodenetwork_mac' in search_vals:
                sites = filter(lambda site: \
                               search_vals['nodenetwork_mac'] in site['macs'],
                               sites)

        return [site['site_id'] for site in sites]

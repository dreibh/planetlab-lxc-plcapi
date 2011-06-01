ALTER TABLE nodes ADD COLUMN last_time_spent_online integer;
ALTER TABLE nodes ADD COLUMN last_time_spent_offline integer;

DROP VIEW view_nodes;
CREATE OR REPLACE VIEW view_nodes AS
SELECT
nodes.node_id,
nodes.node_type,
nodes.hostname,
nodes.site_id,
nodes.boot_state,
nodes.run_level,
nodes.deleted,
nodes.model,
nodes.boot_nonce,
nodes.version,
nodes.verified,
nodes.ssh_rsa_key,
nodes.key,
CAST(date_part('epoch', nodes.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', nodes.last_updated) AS bigint) AS last_updated,
CAST(date_part('epoch', nodes.last_contact) AS bigint) AS last_contact,  
CAST(date_part('epoch', nodes.last_boot) AS bigint) AS last_boot,  
CAST(date_part('epoch', nodes.last_download) AS bigint) AS last_download,  
CAST(date_part('epoch', nodes.last_pcu_reboot) AS bigint) AS last_pcu_reboot,  
CAST(date_part('epoch', nodes.last_pcu_confirmation) AS bigint) AS last_pcu_confirmation,  
nodes.last_time_spent_online,
nodes.last_time_spent_offline,
peer_node.peer_id,
peer_node.peer_node_id,
COALESCE((SELECT interface_ids FROM node_interfaces 
		 WHERE node_interfaces.node_id = nodes.node_id), '{}') 
AS interface_ids,
COALESCE((SELECT nodegroup_ids FROM node_nodegroups 
		 WHERE node_nodegroups.node_id = nodes.node_id), '{}') 
AS nodegroup_ids,
COALESCE((SELECT slice_ids FROM node_slices 
		 WHERE node_slices.node_id = nodes.node_id), '{}') 
AS slice_ids,
COALESCE((SELECT slice_ids_whitelist FROM node_slices_whitelist 
		 WHERE node_slices_whitelist.node_id = nodes.node_id), '{}') 
AS slice_ids_whitelist,
COALESCE((SELECT pcu_ids FROM node_pcus 
		 WHERE node_pcus.node_id = nodes.node_id), '{}') 
AS pcu_ids,
COALESCE((SELECT ports FROM node_pcus
		 WHERE node_pcus.node_id = nodes.node_id), '{}') 
AS ports,
COALESCE((SELECT conf_file_ids FROM node_conf_files
		 WHERE node_conf_files.node_id = nodes.node_id), '{}') 
AS conf_file_ids,
COALESCE((SELECT node_tag_ids FROM node_tags 
		 WHERE node_tags.node_id = nodes.node_id), '{}') 
AS node_tag_ids,
node_session.session_id AS session
FROM nodes
LEFT JOIN peer_node USING (node_id)
LEFT JOIN node_session USING (node_id);

--------------------------------------------------------------------------------

UPDATE plc_db_version SET subversion = 105;

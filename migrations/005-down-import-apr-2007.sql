-- revert migration 005
-- 
-- this is a rather complex example, so for next times, make sure that you
-- * first restore old columns or tables
-- * then create or replace views
-- * and only finally drop new columns and tables
-- otherwise the columns may refuse to get dropped if they are still used by views
--

---------- creations 

ALTER TABLE events ADD object_type text NOT NULL Default 'Unknown';

---------- view changes

-- for some reason these views require to be dropped first
DROP VIEW view_events;
DROP VIEW event_objects;
DROP VIEW view_nodes;
DROP VIEW view_sites;

CREATE OR REPLACE VIEW event_objects AS
SELECT event_id,
array_accum(object_id) AS object_ids
FROM event_object
GROUP BY event_id;

CREATE OR REPLACE VIEW view_events AS
SELECT
events.event_id,
events.person_id,
events.node_id,
events.fault_code,
events.call_name,
events.call,
events.object_type,
events.message,
events.runtime,
CAST(date_part('epoch', events.time) AS bigint) AS time,
COALESCE((SELECT object_ids FROM event_objects WHERE event_objects.event_id = events.event_id), '{}') AS object_ids
FROM events;

CREATE OR REPLACE VIEW view_nodes AS
SELECT
nodes.node_id,
nodes.hostname,
nodes.site_id,
nodes.boot_state,
nodes.deleted,
nodes.model,
nodes.boot_nonce,
nodes.version,
nodes.ssh_rsa_key,
nodes.key,
CAST(date_part('epoch', nodes.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', nodes.last_updated) AS bigint) AS last_updated,
peer_node.peer_id,
peer_node.peer_node_id,
COALESCE((SELECT nodenetwork_ids FROM node_nodenetworks WHERE node_nodenetworks.node_id = nodes.node_id), '{}') AS nodenetwork_ids,
COALESCE((SELECT nodegroup_ids FROM node_nodegroups WHERE node_nodegroups.node_id = nodes.node_id), '{}') AS nodegroup_ids,
COALESCE((SELECT slice_ids FROM node_slices WHERE node_slices.node_id = nodes.node_id), '{}') AS slice_ids,
COALESCE((SELECT pcu_ids FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS pcu_ids,
COALESCE((SELECT ports FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS ports,
COALESCE((SELECT conf_file_ids FROM node_conf_files WHERE node_conf_files.node_id = nodes.node_id), '{}') AS conf_file_ids,
node_session.session_id AS session
FROM nodes
LEFT JOIN peer_node USING (node_id)
LEFT JOIN node_session USING (node_id);

CREATE OR REPLACE VIEW view_sites AS
SELECT
sites.site_id,
sites.login_base,
sites.name,
sites.abbreviated_name,
sites.deleted,
sites.enabled,
sites.is_public,
sites.max_slices,
sites.max_slivers,
sites.latitude,
sites.longitude,
sites.url,
CAST(date_part('epoch', sites.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', sites.last_updated) AS bigint) AS last_updated,
peer_site.peer_id,
peer_site.peer_site_id,
COALESCE((SELECT person_ids FROM site_persons WHERE site_persons.site_id = sites.site_id), '{}') AS person_ids,
COALESCE((SELECT node_ids FROM site_nodes WHERE site_nodes.site_id = sites.site_id), '{}') AS node_ids,
COALESCE((SELECT address_ids FROM site_addresses WHERE site_addresses.site_id = sites.site_id), '{}') AS address_ids,
COALESCE((SELECT slice_ids FROM site_slices WHERE site_slices.site_id = sites.site_id), '{}') AS slice_ids,
COALESCE((SELECT pcu_ids FROM site_pcus WHERE site_pcus.site_id = sites.site_id), '{}') AS pcu_ids
FROM sites
LEFT JOIN peer_site USING (site_id);

---------- deletions

ALTER TABLE sites DROP COLUMN ext_consortium_id;

ALTER TABLE nodes DROP COLUMN last_contact;

DROP INDEX initscripts_name_idx;
DROP TABLE initscripts;

ALTER TABLE events DROP COLUMN auth_type;

ALTER TABLE event_object DROP COLUMN object_type;

---------- revert subversion

UPDATE plc_db_version SET subversion = 4;
SELECT subversion from plc_db_version;

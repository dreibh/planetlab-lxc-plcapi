--
-- migration 008
-- import from Princeton codebase on august 2007 28
-- slice instantiation 'nm-controller'
-- * white lists
-- 

INSERT INTO slice_instantiations (instantiation) VALUES ('nm-controller'); -- NM Controller

--------------------------------------------------------------------------------
-- Slice whitelist
--------------------------------------------------------------------------------
-- slice whitelist on nodes
CREATE TABLE node_slice_whitelist (
    node_id integer REFERENCES nodes NOT NULL, -- Node id of whitelist
    slice_id integer REFERENCES slices NOT NULL, -- Slice id thats allowd on this node
    PRIMARY KEY (node_id, slice_id)
) WITH OIDS;
CREATE INDEX node_slice_whitelist_node_id_idx ON node_slice_whitelist (node_id);
CREATE INDEX node_slice_whitelist_slice_id_idx ON node_slice_whitelist (slice_id);

-- Slices on each node
CREATE VIEW node_slices_whitelist AS
SELECT node_id,
array_accum(slice_id) AS slice_ids_whitelist
FROM node_slice_whitelist
GROUP BY node_id;

DROP VIEW view_nodes;


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
CAST(date_part('epoch', nodes.last_contact) AS bigint) AS last_contact,  
peer_node.peer_id,
peer_node.peer_node_id,
COALESCE((SELECT nodenetwork_ids FROM node_nodenetworks WHERE node_nodenetworks.node_id = nodes.node_id), '{}') AS nodenetwork_ids,
COALESCE((SELECT nodegroup_ids FROM node_nodegroups WHERE node_nodegroups.node_id = nodes.node_id), '{}') AS nodegroup_ids,
COALESCE((SELECT slice_ids FROM node_slices WHERE node_slices.node_id = nodes.node_id), '{}') AS slice_ids,
COALESCE((SELECT slice_ids_whitelist FROM node_slices_whitelist WHERE node_slices_whitelist.node_id = nodes.node_id), '{}') AS slice_ids_whitelist,
COALESCE((SELECT pcu_ids FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS pcu_ids,
COALESCE((SELECT ports FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS ports,
COALESCE((SELECT conf_file_ids FROM node_conf_files WHERE node_conf_files.node_id = nodes.node_id), '{}') AS conf_file_ids,
node_session.session_id AS session
FROM nodes
LEFT JOIN peer_node USING (node_id)
LEFT JOIN node_session USING (node_id);

---------- bump subversion

UPDATE plc_db_version SET subversion = 8;
SELECT subversion from plc_db_version;

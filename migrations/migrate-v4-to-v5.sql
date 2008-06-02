-- $Id$
--
-- this is the script to migrate from 4.2 to 5.0
--

----------------------------------------
-- rename nodenetwork into interface
----------------------------------------

ALTER TABLE nodenetworks RENAME TO interfaces;
ALTER TABLE interfaces RENAME COLUMN nodenetwork_id TO interface_id;

ALTER INDEX nodenetworks_node_id_idx RENAME TO interfaces_node_id_idx;

-- xxx need manual merge -> turn into tag_type
--ALTER TABLE nodenetwork_setting_types RENAME TO interface_setting_types;
--ALTER TABLE interface_setting_types RENAME COLUMN nodenetwork_setting_type_id TO interface_setting_type_id;

ALTER TABLE nodenetwork_setting RENAME TO interface_setting;

-- views
ALTER TABLE nodenetworks_ordered RENAME TO interfaces_ordered;
ALTER TABLE interfaces_ordered RENAME COLUMN nodenetwork_id TO interface_id;

ALTER TABLE node_nodenetworks RENAME TO node_interfaces;
ALTER TABLE node_interfaces RENAME COLUMN nodenetwork_ids TO interface_ids;

ALTER TABLE nodenetwork_settings RENAME TO interface_settings;
ALTER TABLE interface_settings RENAME COLUMN nodenetwork_id TO interface_id;
ALTER TABLE interface_settings RENAME COLUMN nodenetwork_setting_ids TO interface_setting_ids;

ALTER TABLE view_nodenetwork_settings RENAME TO view_interface_settings;
ALTER TABLE view_interface_settings RENAME COLUMN nodenetwork_setting_id TO interface_setting_id;
ALTER TABLE view_interface_settings RENAME COLUMN nodenetwork_id TO interface_id;
-- xxx need manual merge -> turn into tag_type
--ALTER TABLE view_interface_settings RENAME COLUMN nodenetwork_setting_type_id TO interface_setting_type_id;

ALTER TABLE view_nodenetworks RENAME TO view_interfaces;
ALTER TABLE view_interfaces RENAME COLUMN nodenetwork_id TO interface_id;
ALTER TABLE view_interfaces RENAME COLUMN nodenetwork_setting_ids TO interface_setting_ids;

ALTER TABLE view_nodes RENAME COLUMN nodenetwork_ids TO interface_ids;

----------------------------------------
-- node tags
----------------------------------------
CREATE TABLE tag_types ...
CREATE TABLE node_tag ...

---------- related views
CREATE OR REPLACE VIEW node_tags AS ...
CREATE OR REPLACE VIEW view_node_tags AS ... 

----------------------------------------
-- nodegroups
-- xxx - todo 
-- a more usable migration script would need to capture more data
----------------------------------------
DROP TABLE IF EXISTS nodegroups CASCADE;

-- Node groups
CREATE TABLE nodegroups ... 
CREATE OR REPLACE VIEW nodegroup_node AS ...
CREATE OR REPLACE VIEW nodegroup_nodes AS ...
CREATE OR REPLACE VIEW node_nodegroups AS ...
CREATE OR REPLACE VIEW view_nodegroups AS

----------------------------------------
-- the nodes view
----------------------------------------
DROP VIEW view_nodes;
CREATE OR REPLACE VIEW view_nodes AS ...

----------------------------------------
-- ilinks
----------------------------------------
--CREATE TABLE link_types ...
CREATE TABLE ilink ...

CREATE OR REPLACE VIEW ilinks AS ...
CREATE OR REPLACE VIEW ilink_src_node AS ...
CREATE OR REPLACE VIEW ilink_nodes AS ...

----------------------------------------
-- update versioning
----------------------------------------
UPDATE plc_db_version SET version=5, subversion=0;

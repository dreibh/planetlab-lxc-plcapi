--
-- $Id$
--
-- this is part of the script to migrate from 4.2 to 5.0
--

-------------------- VIEWS :
-- we want the views to get out of our way, i.e. to drop all views; 
-- the views will be reinstantiated later upon loading of planetlab5.sql

-- this lists all views
CREATE OR REPLACE VIEW all_views AS
    SELECT c.relname FROM pg_catalog.pg_class c
       LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
          WHERE c.relkind IN ('v','') AND n.nspname in ('public')
	     AND pg_catalog.pg_table_is_visible(c.oid);

-- shows in logfile
select * from all_views;

-- this one version almost works, but somehow does not, could not figure why
CREATE OR REPLACE FUNCTION drop_all_views () RETURNS INTEGER AS $$
    DECLARE 
        row all_views%ROWTYPE;
    BEGIN
        FOR row IN SELECT * FROM all_views where relname != 'all_views' LOOP
	   RAISE NOTICE 'Dropping %',row.relname;
           EXECUTE 'DROP VIEW ' || row.relname || ' CASCADE' ;
	END LOOP;
        RETURN 0;	
    END;
$$ LANGUAGE 'plpgsql';

-- SELECT drop_all_views();

-- so let's have it the boring way
DROP VIEW address_address_types CASCADE;
DROP VIEW conf_file_nodegroups CASCADE;
DROP VIEW conf_file_nodes CASCADE;
DROP VIEW dummybox_nodes CASCADE;
DROP VIEW event_objects CASCADE;
DROP VIEW node_conf_files CASCADE;
DROP VIEW node_nodegroups CASCADE;
DROP VIEW interfaces_ordered CASCADE;
-- caught by some previous cascade -- DROP VIEW node_interfaces CASCADE;
DROP VIEW node_pcus CASCADE;
DROP VIEW node_slices CASCADE;
DROP VIEW node_slices_whitelist CASCADE;
DROP VIEW nodegroup_conf_files CASCADE;
DROP VIEW nodegroup_nodes CASCADE;
DROP VIEW interface_settings CASCADE;
DROP VIEW pcu_nodes CASCADE;
DROP VIEW pcu_protocol_types CASCADE;
DROP VIEW peer_keys CASCADE;
DROP VIEW peer_nodes CASCADE;
DROP VIEW peer_persons CASCADE;
DROP VIEW peer_sites CASCADE;
DROP VIEW peer_slices CASCADE;
DROP VIEW person_keys CASCADE;
DROP VIEW person_roles CASCADE;
DROP VIEW person_site_ordered CASCADE;
-- caught by some previous cascade -- DROP VIEW person_sites CASCADE;
DROP VIEW person_slices CASCADE;
DROP VIEW site_addresses CASCADE;
DROP VIEW site_nodes CASCADE;
DROP VIEW site_pcus CASCADE;
DROP VIEW site_persons CASCADE;
DROP VIEW site_slices CASCADE;
DROP VIEW slice_attributes CASCADE;
DROP VIEW slice_nodes CASCADE;
DROP VIEW slice_persons CASCADE;
DROP VIEW slivers CASCADE;
-- caught by some previous cascade -- DROP VIEW view_addresses CASCADE;
-- caught by some previous cascade -- DROP VIEW view_conf_files CASCADE;
-- caught by some previous cascade -- DROP VIEW view_dummyboxes CASCADE;
DROP VIEW view_event_objects CASCADE;
-- caught by some previous cascade -- DROP VIEW view_events CASCADE;
DROP VIEW view_keys CASCADE;
-- caught by some previous cascade -- DROP VIEW view_nodegroups CASCADE;
DROP VIEW view_interface_settings CASCADE;
-- caught by some previous cascade -- DROP VIEW view_interfaces CASCADE;
-- caught by some previous cascade -- DROP VIEW view_nodes CASCADE;
-- caught by some previous cascade -- DROP VIEW view_pcu_types CASCADE;
-- caught by some previous cascade -- DROP VIEW view_pcus CASCADE;
-- caught by some previous cascade -- DROP VIEW view_peers CASCADE;
-- caught by some previous cascade -- DROP VIEW view_persons CASCADE;
DROP VIEW view_sessions CASCADE;
-- caught by some previous cascade -- DROP VIEW view_sites CASCADE;
DROP VIEW view_slice_attributes CASCADE;
-- caught by some previous cascade -- DROP VIEW view_slices CASCADE;

-- shows in logfile
select * from all_views;


-------------------- TAG TYPES
--- merge former slice attribute types and setting attribute types into tagtypes

--- the tag_types table is obtained from the former slice_attribute_types table 
ALTER TABLE tag_types RENAME COLUMN name TO tagname;
--- former slice_attribute_types had no 'category'
ALTER TABLE tag_types ADD COLUMN category TEXT NOT NULL DEFAULT 'slice/legacy';
--- change default now that the column is filled
ALTER TABLE tag_types ALTER COLUMN category SET DEFAULT 'general';

--- append in tag_types the contents of nodenetwork_setting_types
insert into tag_types (tagname,description,min_role_id,category) select name,description,min_role_id,'interface/legacy' from interface_setting_types;

--- former nodenetwork_setting_type_id are now renumbered, need to fix interface_setting accordingly

-- old_index -> new_index relation
CREATE OR REPLACE VIEW index_renumber AS
   SELECT 
      interface_setting_types.interface_setting_type_id AS old_index,	
      tag_types.tag_type_id AS new_index 
   FROM 
      interface_setting_types INNER JOIN tag_types  
      ON interface_setting_types.name = tag_types.tagname;

-- need to temporarily drop constraint on interface_setting_type_id
ALTER TABLE interface_setting DROP CONSTRAINT interface_setting_interface_setting_type_id_fkey;

-- do the transcoding
UPDATE interface_setting 
   SET interface_setting_type_id = 
      (select new_index from index_renumber where old_index=interface_setting_type_id);

-- alter column nam to reflect change
ALTER TABLE interface_setting RENAME interface_setting_type_id TO tag_type_id;

-- add contraint again
ALTER TABLE interface_setting ADD CONSTRAINT interface_setting_tag_type_id_fkey 
    FOREIGN KEY (tag_type_id) references tag_types(tag_type_id) ;

--- cleanup
drop view index_renumber;

-- drop former interface_setting_types altogether
drop table interface_setting_types;

-------------------- NEW STUFF

CREATE TABLE ilink (
       ilink_id serial PRIMARY KEY,				-- id
       tag_type_id integer REFERENCES tag_types,		-- id of the tag type
       src_interface_id integer REFERENCES interfaces not NULL,	-- id of src interface
       dst_interface_id integer REFERENCES interfaces NOT NULL, -- id of dst interface
       value text						-- optional value on the link
) WITH OIDS;


CREATE TABLE node_tag (
    node_tag_id serial PRIMARY KEY,			-- ID
    node_id integer REFERENCES nodes NOT NULL,		-- node id
    tag_type_id integer REFERENCES tag_types,		-- tag type id
    tagvalue text					-- value attached
) WITH OIDS;

----------------------------------------
-- nodegroups
----------------------------------------
--- xxx - need to capture this first
--- xxx would dump some python script to capture current nodegroups...

--- xxx would maybe like to preserve it in nodegroups_v4 or something
DROP TABLE IF EXISTS nodegroups CASCADE;
DROP TABLE IF EXISTS nodegroup_node CASCADE;

CREATE TABLE nodegroups (
    nodegroup_id serial PRIMARY KEY,		-- Group identifier
    groupname text UNIQUE NOT NULL,		-- Group name 
    tag_type_id integer REFERENCES tag_types,	-- node is in nodegroup if it has this tag defined
    tagvalue text NOT NULL			-- with this value attached
) WITH OIDS;

-------------
-- display constraints

CREATE OR REPLACE VIEW all_constraints AS
    SELECT * FROM pg_catalog.pg_constraint c
       LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.connamespace
       LEFT JOIN pg_catalog.pg_class t ON t.oid = c.conrelid
          WHERE c.contype IN ('c','f','p','u') AND n.nspname in ('public')
	     AND pg_catalog.pg_table_is_visible(c.oid);

-- cleanup
drop view all_views;

--- versioning (plc_db_version): ignore for now, so we keep both entries (v4 and v5)

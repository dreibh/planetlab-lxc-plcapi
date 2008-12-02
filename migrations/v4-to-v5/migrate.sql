-- Thierry Parmentelat - INRIA
-- 
-- $Id$
--
-- this is part of the script to migrate from 4.2 to 5.0
-- 
-- most of the renamings have taken place already when this script is invoked
--

----------------------------------------
-- views
----------------------------------------
-- we want the views to get out of our way, i.e. to drop all views; 
-- the views will be reinstantiated later upon loading of planetlab5.sql

-- this lists all views
CREATE OR REPLACE VIEW mgn_all_views AS
    SELECT c.relname FROM pg_catalog.pg_class c
       LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
          WHERE c.relkind IN ('v','') AND n.nspname in ('public')
	     AND pg_catalog.pg_table_is_visible(c.oid);

-- shows in logfile
select * from mgn_all_views;

-- this one version almost works, but somehow does not, could not figure why
CREATE OR REPLACE FUNCTION mgn_drop_all_views () RETURNS INTEGER AS $$
    DECLARE 
        row mgn_all_views%ROWTYPE;
    BEGIN
        FOR row IN SELECT * FROM mgn_all_views where relname != 'mgn_all_views' LOOP
	   RAISE NOTICE 'Dropping %',row.relname;
           EXECUTE 'DROP VIEW ' || row.relname || ' CASCADE' ;
	END LOOP;
        RETURN 0;	
    END;
$$ LANGUAGE 'plpgsql';

-- SELECT mgn_drop_all_views();

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
DROP VIEW interface_tags CASCADE;
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
DROP VIEW slice_tags CASCADE;
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
DROP VIEW view_interface_tags CASCADE;
-- caught by some previous cascade -- DROP VIEW view_interfaces CASCADE;
-- caught by some previous cascade -- DROP VIEW view_nodes CASCADE;
-- caught by some previous cascade -- DROP VIEW view_pcu_types CASCADE;
-- caught by some previous cascade -- DROP VIEW view_pcus CASCADE;
-- caught by some previous cascade -- DROP VIEW view_peers CASCADE;
-- caught by some previous cascade -- DROP VIEW view_persons CASCADE;
DROP VIEW view_sessions CASCADE;
-- caught by some previous cascade -- DROP VIEW view_sites CASCADE;
DROP VIEW view_slice_tags CASCADE;
-- caught by some previous cascade -- DROP VIEW view_slices CASCADE;

-- shows in logfile
select * from mgn_all_views;

-- cleanup migration utilities
drop view mgn_all_views;
drop function mgn_drop_all_views ();

----------------------------------------
-- tag types
----------------------------------------
--- merge former slice attribute types and setting attribute types into tagtypes

---------- slice attributes

--- the tag_types table is obtained from the former slice_attribute_types table 
ALTER TABLE tag_types RENAME COLUMN name TO tagname;
--- former slice_attribute_types had no 'category'
ALTER TABLE tag_types ADD COLUMN category TEXT NOT NULL DEFAULT 'slice/legacy';

--- append in tag_types the contents of nodenetwork_setting_types
INSERT INTO tag_types (tagname,description,min_role_id,category) 
       SELECT name,description,min_role_id,'interface/legacy' FROM interface_tag_types;

---------- interface settings

--- former nodenetwork_setting_type_id are now renumbered, need to fix interface_tag accordingly

-- old_index -> new_index relation
CREATE OR REPLACE VIEW mgn_setting_renumber AS
   SELECT 
      interface_tag_types.interface_tag_type_id AS old_index,	
      tag_types.tag_type_id AS new_index 
   FROM 
      interface_tag_types INNER JOIN tag_types  
      ON interface_tag_types.name = tag_types.tagname;

-- need to temporarily drop constraint on interface_tag_type_id
ALTER TABLE interface_tag DROP CONSTRAINT interface_tag_interface_tag_type_id_fkey;

-- do the transcoding
UPDATE interface_tag 
   SET interface_tag_type_id = 
      (select new_index from mgn_setting_renumber where old_index=interface_tag_type_id);

-- alter column name to reflect change
ALTER TABLE interface_tag RENAME interface_tag_type_id TO tag_type_id;

-- add constraint again
ALTER TABLE interface_tag ADD CONSTRAINT interface_tag_tag_type_id_fkey 
    FOREIGN KEY (tag_type_id) references tag_types(tag_type_id) ;

-- drop former interface_tag_types altogether
drop view mgn_setting_renumber;
drop table interface_tag_types;

---------- node tags

CREATE TABLE node_tag (
    node_tag_id serial PRIMARY KEY,			-- ID
    node_id integer REFERENCES nodes NOT NULL,		-- node id
    tag_type_id integer REFERENCES tag_types,		-- tag type id
    tagvalue text					-- value attached
) WITH OIDS;


----------------------------------------
-- ilinks
----------------------------------------
CREATE TABLE ilink (
       ilink_id serial PRIMARY KEY,				-- id
       tag_type_id integer REFERENCES tag_types,		-- id of the tag type
       src_interface_id integer REFERENCES interfaces not NULL,	-- id of src interface
       dst_interface_id integer REFERENCES interfaces NOT NULL, -- id of dst interface
       value text						-- optional value on the link
) WITH OIDS;

----------------------------------------
-- nodegroups
----------------------------------------

---------- nodegroups table - start
-- nodegroup_id is preserved for conf_files and other references
-- former nodegroups table was (nodegroup_id,name,description)
-- new table is	now	       (nodegroup_id, groupname, tag_type_id, tagvalue)

-- rename column
ALTER TABLE nodegroups RENAME name TO groupname;

---------- create missing tag types
-- change default for the entries about to be created
ALTER TABLE tag_types ALTER COLUMN category SET DEFAULT 'nodegroup/migration';

-- do it
INSERT INTO tag_types (tagname)
   SELECT DISTINCT tagname FROM mgn_site_nodegroup 
      WHERE tagname NOT IN (SELECT tagname from tag_types);

-- xxx drop description in former nodegroups for now, 
-- but could have been attached to newly created tag types first
ALTER TABLE nodegroups DROP COLUMN description;

---------- set the right tags so as to recover former nodegroups
INSERT INTO node_tag (node_id, tag_type_id, tagvalue)
   SELECT node_id, tag_type_id, tagvalue FROM
      nodegroup_node LEFT JOIN nodegroups USING (nodegroup_id) 
         INNER JOIN mgn_site_nodegroup USING (groupname)
	    LEFT JOIN tag_types using (tagname); 

---------- nodegroups table - conclusion
ALTER TABLE nodegroups ADD COLUMN tag_type_id INTEGER;
ALTER TABLE nodegroups ADD COLUMN tagvalue TEXT;

CREATE OR REPLACE VIEW mgn_nodegroups AS
   SELECT groupname, tag_types.tag_type_id, mgn_site_nodegroup.tagvalue 
      FROM nodegroups INNER JOIN mgn_site_nodegroup USING (groupname) 
         INNER JOIN tag_types USING (tagname);

UPDATE nodegroups SET tag_type_id = (SELECT tag_type_id FROM mgn_nodegroups WHERE nodegroups.groupname=mgn_nodegroups.groupname);
UPDATE nodegroups SET tagvalue = (SELECT tagvalue FROM mgn_nodegroups WHERE nodegroups.groupname=mgn_nodegroups.groupname);

-- install corresponding constraints
ALTER TABLE nodegroups ADD CONSTRAINT nodegroups_tag_type_id_fkey
   FOREIGN KEY (tag_type_id) REFERENCES tag_types (tag_type_id);  

--- change default now that the column is filled
ALTER TABLE tag_types ALTER COLUMN category SET DEFAULT 'general';

-- cleanup the nodegroup area
drop view mgn_nodegroups;
drop table mgn_site_nodegroup;
drop table nodegroup_node;

----------------------------------------
-- boot states
----------------------------------------
-- create new ones
INSERT INTO boot_states (boot_state) VALUES ('safeboot');
INSERT INTO boot_states (boot_state) VALUES ('failboot');
INSERT INTO boot_states (boot_state) VALUES ('disabled');
INSERT INTO boot_states (boot_state) VALUES ('install');
INSERT INTO boot_states (boot_state) VALUES ('reinstall');

-- map old ones
UPDATE nodes SET boot_state='failboot' WHERE boot_state='dbg';
UPDATE nodes SET boot_state='safeboot' WHERE boot_state='diag';
UPDATE nodes SET boot_state='disabled' WHERE boot_state='disable';
UPDATE nodes SET boot_state='install' WHERE boot_state='inst';
UPDATE nodes SET boot_state='reinstall' WHERE boot_state='rins';
UPDATE nodes SET boot_state='reinstall' WHERE boot_state='new';
UPDATE nodes SET boot_state='failboot' WHERE boot_state='rcnf';

-- delete old ones
DELETE FROM boot_states WHERE boot_state='dbg';
DELETE FROM boot_states WHERE boot_state='diag';
DELETE FROM boot_states WHERE boot_state='disable';
DELETE FROM boot_states WHERE boot_state='inst';
DELETE FROM boot_states WHERE boot_state='rins';
DELETE FROM boot_states WHERE boot_state='new';
DELETE FROM boot_states WHERE boot_state='rcnf';

-- ----------------------------------------
-- -- debug/information : display current constraints
-- ----------------------------------------
-- CREATE OR REPLACE VIEW mgn_all_constraints AS
--     SELECT * FROM pg_catalog.pg_constraint c
--        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.connamespace
--        LEFT JOIN pg_catalog.pg_class t ON t.oid = c.conrelid
--           WHERE c.contype IN ('c','f','p','u') AND n.nspname in ('public')
-- 	     AND pg_catalog.pg_table_is_visible(c.oid);
-- 
-- select * from mgn_all_constraints;
--
-- drop view mgn_all_constraints;

--- versioning (plc_db_version): ignore for now, so we keep both entries (v4 and v5)

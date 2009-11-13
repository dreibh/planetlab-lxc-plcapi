-- 
-- purpose: provide a way to delete the additions added by the up script.
-- NOTE: this does not leave the DB in a usable state, since it drops the view_sites and view_persons;
-- 

DROP VIEW view_site_tags;
DROP VIEW view_sites;
DROP VIEW site_tags;
DROP TABLE site_tag;

DROP VIEW view_person_tags;
DROP VIEW view_persons;
DROP VIEW person_tags;
DROP TABLE person_tag;

UPDATE plc_db_version SET subversion = 0;

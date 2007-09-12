-- IMPORTANT NOTICE
--
-- this down script is provided for convenience only
-- DO NOT USE on an operational site
-- the change in migration 003 involves creating 
-- the new view view_nodenetworks for fetching instances
-- of NodeNetworks
-- AND to alter NodeNetworks.py accordingly
-- so this change cannot be easily undone 
-- unless you also revert the API itself

DROP VIEW view_nodenetworks;

DROP VIEW view_nodenetwork_settings;

DROP VIEW nodenetwork_settings;

DROP TABLE nodenetwork_setting;

DROP TABLE nodenetwork_setting_types;

-- deflate subversion
UPDATE plc_db_version SET subversion = 2;
SELECT subversion from plc_db_version;

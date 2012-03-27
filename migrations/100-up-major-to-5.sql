-- myplc v5.0 starts with (5,100)
-- the expected former values would be (4,11)
--
-- if you somehow start from a 4.3 not entirely up-dated to rc17, 
-- then manually run
-- http://git.onelab.eu/?p=plcapi.git;a=blob;f=migrations/011-up-site-and-person-tags.sql;hb=refs/heads/4.3
-- 
UPDATE plc_db_version SET version = 5;
UPDATE plc_db_version SET subversion = 100;

-- $Id$
-- $URL$
-- myplc v5.0 starts with (5,100)
-- the expected former values would be (4,11)
--
-- if you somehow start from a 4.3 not entirely up-dated to rc17, 
-- then manually run
-- http://svn.planet-lab.org/svn/PLCAPI/branches/4.3/migrations/011-up-site-and-person-tags.sql
-- 
UPDATE plc_db_version SET version = 5;
UPDATE plc_db_version SET subversion = 100;

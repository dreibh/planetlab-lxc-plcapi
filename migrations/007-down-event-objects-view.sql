--
-- migration 007 - revert
--

DROP VIEW view_event_objects;

---------- revert subversion

UPDATE plc_db_version SET subversion = 6;
SELECT subversion from plc_db_version;


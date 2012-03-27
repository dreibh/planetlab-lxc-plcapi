-- revert cleanup on node_types
INSERT INTO node_types VALUES ('dummynet');

UPDATE nodes SET node_type='regular' WHERE node_type='reservable';
DELETE FROM node_types WHERE node_type='reservable';

-- drop new tables
DROP VIEW view_leases;
DROP VIEW view_all_leases;
DROP TABLE leases;

DROP FUNCTION IF EXISTS overlapping_trigger();

--------------------------------------------------
UPDATE plc_db_version SET subversion = 100;

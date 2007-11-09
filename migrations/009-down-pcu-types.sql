--
-- 009 revert
--

DROP VIEW view_pcu_types;

DROP VIEW pcu_type_ports;

DROP TABLE pcu_type_port;

DROP TABLE pcu_types; 

UPDATE plc_db_version SET subversion = 7;

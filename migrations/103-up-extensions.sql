CREATE TABLE plc_db_extensions (
    name text NOT NULL PRIMARY KEY,
    version integer NOT NULL
) WITH OIDS;

UPDATE plc_db_version SET subversion = 103;

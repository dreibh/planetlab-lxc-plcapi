-- this is mostly sample code
-- since subversion is also created by the migration code in plc.d/db

ALTER TABLE plc_db_version ADD subversion integer DEFAULT 0;

-- Add plc_db_version.subversion field
ALTER TABLE plc_db_version ADD subversion integer NOT NULL DEFAULT 0;

-- Bump subversion
UPDATE plc_db_version SET subversion = 1;

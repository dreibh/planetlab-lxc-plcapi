-- Remove NOT NULL constraint from creator_person_id in case the
-- creator is deleted.
ALTER TABLE slices ALTER creator_person_id DROP NOT NULL;

-- Bump subversion
UPDATE plc_db_version SET subversion = 2;

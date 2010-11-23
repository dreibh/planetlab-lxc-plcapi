-- recreate the min_role_id column
ALTER TABLE tag_types ADD COLUMN min_role_id integer REFERENCES roles;

-- compute the highest role available for each tag_type and store it as min_role_id
CREATE OR REPLACE VIEW tag_type_max_role_id AS
SELECT tag_type_id, max(role_id) from tag_type_role GROUP BY tag_type_id;

-- tag_types that have at least one role in the new model get the max
UPDATE tag_types 
SET min_role_id = tag_type_max_role_id.max
FROM tag_type_max_role_id WHERE tag_type_max_role_id.tag_type_id = tag_types.tag_type_id;

-- the ones with no roles end up with min_role_id=10
UPDATE tag_types
SET min_role_id=10
WHERE min_role_id IS NULL;

DELETE VIEW tag_type_max_role_id;

DROP TABLE tag_type_role CASCADE;
-- done by cascade
--DROP VIEW view_tag_types;
--DROP VIEW tag_type_roles;

DELETE from roles WHERE name='node';

--------------------
UPDATE plc_db_version SET subversion = 103;

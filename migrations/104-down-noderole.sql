-- reverting....
DELETE from roles WHERE name='node';

-- recreate the min_role_id column
ALTER TABLE tag_types ADD COLUMN min_role_id integer REFERENCES roles;

-- compute the highest role available for each tag_type and store it as min_role_id
-- xxx todo

--- tmp - set to something so we can run down&up again
UPDATE tag_types SET min_role_id=10;
UPDATE tag_types SET min_role_id=20 WHERE tag_type_id%2=0;

DROP TABLE tag_type_role CASCADE;
-- done by cascade
--DROP VIEW view_tag_types;
--DROP VIEW tag_type_roles;

--------------------
UPDATE plc_db_version SET subversion = 103;

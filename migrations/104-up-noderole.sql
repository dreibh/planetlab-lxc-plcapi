-- changing the permission model on tags
-- we replace the single 'min_role_id' field attached to tag_types
-- with a set of roles


-- create a separate table to keep the tag-type x role relationship
CREATE TABLE tag_type_role (
    tag_type_id integer REFERENCES tag_types NOT NULL,	-- tag_type ID
    role_id integer REFERENCES roles NOT NULL,		-- role ID
    PRIMARY KEY (tag_type_id, role_id)
);
CREATE INDEX tag_type_role_tag_type_id_idx ON tag_type_role (tag_type_id);
CREATE INDEX tag_type_role_role_id_idx ON tag_type_role (role_id);

-- fill this from the former min_role_id field in the tag_types table
-- add all roles lower or equal to the min_role_id
INSERT INTO tag_type_role ("tag_type_id","role_id") SELECT tag_type_id,role_id FROM tag_types,roles where role_id<=min_role_id;

-- we can now drop the min_role_id column
ALTER TABLE tag_types DROP COLUMN min_role_id CASCADE;

-- create views to expose roles
CREATE OR REPLACE VIEW tag_type_roles AS
SELECT tag_type_id,
array_accum(role_id) AS role_ids,
array_accum(roles.name) AS roles
FROM tag_type_role 
LEFT JOIN roles USING (role_id)
GROUP BY tag_type_id;

CREATE OR REPLACE VIEW view_tag_types AS
SELECT 
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
COALESCE((SELECT role_ids FROM tag_type_roles WHERE tag_type_roles.tag_type_id = tag_types.tag_type_id), '{}') AS role_ids,
COALESCE((SELECT roles FROM tag_type_roles WHERE tag_type_roles.tag_type_id = tag_types.tag_type_id), '{}') AS roles
FROM tag_types; 


-- remove min_role_id from the object views
CREATE OR REPLACE VIEW view_person_tags AS
SELECT
person_tag.person_tag_id,
person_tag.person_id,
persons.email,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
person_tag.value
FROM person_tag 
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN persons USING (person_id);

CREATE OR REPLACE VIEW view_site_tags AS
SELECT
site_tag.site_tag_id,
site_tag.site_id,
sites.login_base,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
site_tag.value
FROM site_tag 
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN sites USING (site_id);

CREATE OR REPLACE VIEW view_interface_tags AS
SELECT
interface_tag.interface_tag_id,
interface_tag.interface_id,
interfaces.ip,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
interface_tag.value
FROM interface_tag
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN interfaces USING (interface_id);

CREATE OR REPLACE VIEW view_node_tags AS
SELECT
node_tag.node_tag_id,
node_tag.node_id,
nodes.hostname,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
node_tag.value
FROM node_tag 
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN nodes USING (node_id);

CREATE OR REPLACE VIEW view_slice_tags AS
SELECT
slice_tag.slice_tag_id,
slice_tag.slice_id,
slice_tag.node_id,
slice_tag.nodegroup_id,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
slice_tag.value,
slices.name
FROM slice_tag
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN slices USING (slice_id);

-- same for ilinks
CREATE OR REPLACE VIEW view_ilinks AS
SELECT * FROM tag_types 
INNER JOIN ilink USING (tag_type_id);

-- use this to allow nodes to set slice tags
INSERT INTO roles (role_id, name) VALUES (50, 'node');

--------------------
UPDATE plc_db_version SET subversion = 104;

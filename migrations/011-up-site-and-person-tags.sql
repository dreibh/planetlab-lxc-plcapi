--
-- PlanetLab
--
-- migration 001
--
-- purpose: provide tags on site and person objects in db
--
--

-- SITES

CREATE TABLE site_tag (
    site_tag_id serial PRIMARY KEY,			-- ID
    site_id integer REFERENCES sites NOT NULL,		-- site id
    tag_type_id integer REFERENCES tag_types,		-- tag type id
    value text						-- value attached
) WITH OIDS;

CREATE OR REPLACE VIEW site_tags AS
SELECT site_id,
array_accum(site_tag_id) AS site_tag_ids
FROM site_tag
GROUP BY site_id;

CREATE OR REPLACE VIEW view_site_tags AS
SELECT
site_tag.site_tag_id,
site_tag.site_id,
sites.login_base,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
tag_types.min_role_id,
site_tag.value
FROM site_tag 
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN sites USING (site_id);

DROP VIEW view_sites;
CREATE OR REPLACE VIEW view_sites AS
SELECT
sites.site_id,
sites.login_base,
sites.name,
sites.abbreviated_name,
sites.deleted,
sites.enabled,
sites.is_public,
sites.max_slices,
sites.max_slivers,
sites.latitude,
sites.longitude,
sites.url,
sites.ext_consortium_id,
CAST(date_part('epoch', sites.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', sites.last_updated) AS bigint) AS last_updated,
peer_site.peer_id,
peer_site.peer_site_id,
COALESCE((SELECT person_ids FROM site_persons WHERE site_persons.site_id = sites.site_id), '{}') AS person_ids,
COALESCE((SELECT node_ids FROM site_nodes WHERE site_nodes.site_id = sites.site_id), '{}') AS node_ids,
COALESCE((SELECT address_ids FROM site_addresses WHERE site_addresses.site_id = sites.site_id), '{}') AS address_ids,
COALESCE((SELECT slice_ids FROM site_slices WHERE site_slices.site_id = sites.site_id), '{}') AS slice_ids,
COALESCE((SELECT pcu_ids FROM site_pcus WHERE site_pcus.site_id = sites.site_id), '{}') AS pcu_ids,
COALESCE((SELECT site_tag_ids FROM site_tags WHERE site_tags.site_id = sites.site_id), '{}') AS site_tag_ids
FROM sites
LEFT JOIN peer_site USING (site_id);

-- PERSONS

CREATE TABLE person_tag (
    person_tag_id serial PRIMARY KEY,			-- ID
    person_id integer REFERENCES persons NOT NULL,		-- person id
    tag_type_id integer REFERENCES tag_types,		-- tag type id
    value text						-- value attached
) WITH OIDS;

CREATE OR REPLACE VIEW person_tags AS
SELECT person_id,
array_accum(person_tag_id) AS person_tag_ids
FROM person_tag
GROUP BY person_id;

CREATE OR REPLACE VIEW view_person_tags AS
SELECT
person_tag.person_tag_id,
person_tag.person_id,
persons.email,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
tag_types.min_role_id,
person_tag.value
FROM person_tag 
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN persons USING (person_id);

DROP VIEW view_persons;
CREATE OR REPLACE VIEW view_persons AS
SELECT
persons.person_id,
persons.email,
persons.first_name,
persons.last_name,
persons.deleted,
persons.enabled,
persons.password,
persons.verification_key,
CAST(date_part('epoch', persons.verification_expires) AS bigint) AS verification_expires,
persons.title,
persons.phone,
persons.url,
persons.bio,
CAST(date_part('epoch', persons.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', persons.last_updated) AS bigint) AS last_updated,
peer_person.peer_id,
peer_person.peer_person_id,
COALESCE((SELECT role_ids FROM person_roles WHERE person_roles.person_id = persons.person_id), '{}') AS role_ids,
COALESCE((SELECT roles FROM person_roles WHERE person_roles.person_id = persons.person_id), '{}') AS roles,
COALESCE((SELECT site_ids FROM person_sites WHERE person_sites.person_id = persons.person_id), '{}') AS site_ids,
COALESCE((SELECT key_ids FROM person_keys WHERE person_keys.person_id = persons.person_id), '{}') AS key_ids,
COALESCE((SELECT slice_ids FROM person_slices WHERE person_slices.person_id = persons.person_id), '{}') AS slice_ids,
COALESCE((SELECT person_tag_ids FROM person_tags WHERE person_tags.person_id = persons.person_id), '{}') AS person_tag_ids
FROM persons
LEFT JOIN peer_person USING (person_id);


UPDATE plc_db_version SET subversion = 11;

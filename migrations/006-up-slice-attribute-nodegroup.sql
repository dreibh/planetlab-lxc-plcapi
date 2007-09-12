---------- creations 

ALTER TABLE slice_attribute ADD nodegroup_id integer REFERENCES nodegroups;

CREATE INDEX slice_attribute_nodegroup_id_idx ON slice_attribute (nodegroup_id);

---------- view changes

DROP VIEW view_slice_attributes;

CREATE OR REPLACE VIEW view_slice_attributes AS
SELECT
slice_attribute.slice_attribute_id,
slice_attribute.slice_id,
slice_attribute.node_id,
slice_attribute.nodegroup_id,
slice_attribute_types.attribute_type_id,
slice_attribute_types.name,
slice_attribute_types.description,
slice_attribute_types.min_role_id,
slice_attribute.value
FROM slice_attribute
INNER JOIN slice_attribute_types USING (attribute_type_id);


---------- bump subversion

UPDATE plc_db_version SET subversion = 6;
SELECT subversion from plc_db_version;

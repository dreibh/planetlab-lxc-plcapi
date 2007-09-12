--
-- Thierry Parmentelat -- INRIA
--
-- migration 003
-- 
-- purpose : provide a generic mechanism for assigning 
-- nodenetworks (read, network interfaces) with 
-- custom settings
--
-- design
-- mimicks the way slice attributes are being handled, 
-- not that this design is particularly attractive 
-- but let's not add confusion here
-- i.e:
-- (*) nodenetwork_setting_types (see slice_attribute_types) 
-- allows to define a new setting
-- e.g, define one such object for storing wifi SSID
-- 
-- (*) nodenetwork_setting (see slice_attribute)
-- allow to associate a nodenetwork, a nodenetwork_setting_type, and a value
--
-- NOTE. with slice_attributes there is a trick that allows to define 
-- the attribute either on the slice globally or on a particular node only.
-- of course we do not need such a trick

CREATE TABLE nodenetwork_setting_types (
    nodenetwork_setting_type_id serial PRIMARY KEY,	
						-- Setting Type Identifier
    name text UNIQUE NOT NULL,			-- Setting Name    
    description text,				-- Optional Description
    category text NOT NULL,			-- Category, e.g. Wifi, or whatever
    min_role_id integer references roles	-- If set, minimal role required
) WITH OIDS;

CREATE TABLE nodenetwork_setting (
    nodenetwork_setting_id serial PRIMARY KEY,	-- Nodenetwork Setting Identifier
    nodenetwork_id integer REFERENCES nodenetworks NOT NULL,
						-- the nodenetwork this applies to
    nodenetwork_setting_type_id integer REFERENCES nodenetwork_setting_types NOT NULL,
						-- the setting type
    value text
) WITH OIDS;


CREATE OR REPLACE VIEW nodenetwork_settings AS 
SELECT nodenetwork_id,
array_accum(nodenetwork_setting_id) AS nodenetwork_setting_ids
FROM nodenetwork_setting
GROUP BY nodenetwork_id;

CREATE OR REPLACE VIEW view_nodenetwork_settings AS
SELECT
nodenetwork_setting.nodenetwork_setting_id,
nodenetwork_setting.nodenetwork_id,
nodenetwork_setting_types.nodenetwork_setting_type_id,
nodenetwork_setting_types.name,
nodenetwork_setting_types.description,
nodenetwork_setting_types.category,
nodenetwork_setting_types.min_role_id,
nodenetwork_setting.value
FROM nodenetwork_setting
INNER JOIN nodenetwork_setting_types USING (nodenetwork_setting_type_id);

CREATE VIEW view_nodenetworks AS
SELECT
nodenetworks.nodenetwork_id,
nodenetworks.node_id,
nodenetworks.is_primary,
nodenetworks.type,
nodenetworks.method,
nodenetworks.ip,
nodenetworks.mac,
nodenetworks.gateway,
nodenetworks.network,
nodenetworks.broadcast,
nodenetworks.netmask,
nodenetworks.dns1,
nodenetworks.dns2,
nodenetworks.bwlimit,
nodenetworks.hostname,
COALESCE((SELECT nodenetwork_setting_ids FROM nodenetwork_settings WHERE nodenetwork_settings.nodenetwork_id = nodenetworks.nodenetwork_id), '{}') AS nodenetwork_setting_ids
FROM nodenetworks;

-- Bump subversion
UPDATE plc_db_version SET subversion = 3;
SELECT subversion from plc_db_version;

--
-- PlanetLab Central database schema
-- Version 4, PostgreSQL
--
-- Aaron Klingaman <alk@cs.princeton.edu>
-- Reid Moran <rmoran@cs.princeton.edu>
-- Mark Huang <mlhuang@cs.princeton.edu>
-- Tony Mack <tmack@cs.princeton.edu>
--
-- Copyright (C) 2006 The Trustees of Princeton University
--
-- $Id: planetlab4.sql,v 1.2 2006/09/25 18:34:48 mlhuang Exp $
--

--------------------------------------------------------------------------------
-- Aggregates and store procedures
--------------------------------------------------------------------------------

-- Like MySQL GROUP_CONCAT(), this function aggregates values into a
-- PostgreSQL array.
CREATE AGGREGATE array_accum (
    sfunc = array_append,
    basetype = anyelement,
    stype = anyarray,
    initcond = '{}'
);

--------------------------------------------------------------------------------
-- Accounts
--------------------------------------------------------------------------------

-- Accounts
CREATE TABLE persons (
    -- Mandatory
    person_id serial PRIMARY KEY, -- Account identifier
    email text NOT NULL, -- E-mail address
    first_name text NOT NULL, -- First name
    last_name text NOT NULL, -- Last name
    deleted boolean NOT NULL DEFAULT false, -- Has been deleted
    enabled boolean NOT NULL DEFAULT false, -- Has been disabled

    -- Password
    password text NOT NULL, -- Password (md5crypted)
    verification_key text, -- Reset password key
    verification_expires timestamp without time zone,

    -- Optional
    title text, -- Honorific
    phone text, -- Telephone number
    url text, -- Home page
    bio text, -- Biography

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX persons_email_key ON persons (email);

--------------------------------------------------------------------------------
-- Sites
--------------------------------------------------------------------------------

-- Sites
CREATE TABLE sites (
    -- Mandatory
    site_id serial PRIMARY KEY, -- Site identifier
    login_base text NOT NULL, -- Site slice prefix
    name text NOT NULL, -- Site name
    abbreviated_name text NOT NULL, -- Site abbreviated name
    deleted boolean NOT NULL DEFAULT false, -- Has been deleted
    is_public boolean NOT NULL DEFAULT true, -- Shows up in public lists
    max_slices integer NOT NULL DEFAULT 0, -- Maximum number of slices
    max_slivers integer NOT NULL DEFAULT 1000, -- Maximum number of instantiated slivers

    -- Optional
    latitude real,
    longitude real,
    url text,

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX sites_login_base_key ON sites (login_base);

-- Account site membership
CREATE TABLE person_site (
    person_id integer REFERENCES persons, -- Account identifier
    site_id integer REFERENCES sites, -- Site identifier
    is_primary boolean NOT NULL DEFAULT false, -- Is the primary site for this account
    PRIMARY KEY (person_id, site_id)
);
CREATE INDEX person_site_person_id_key ON person_site (person_id);
CREATE INDEX person_site_site_id_key ON person_site (site_id);

-- Ordered by primary site first
CREATE VIEW person_site_ordered AS
SELECT person_id, site_id
FROM person_site
ORDER BY is_primary DESC;

-- Sites that each person is a member of
CREATE VIEW person_sites AS
SELECT person_id,
array_to_string(array_accum(site_id), ',') AS site_ids
FROM person_site_ordered
GROUP BY person_id;

-- Accounts at each site
CREATE VIEW site_persons AS
SELECT site_id,
array_to_string(array_accum(person_id), ',') AS person_ids
FROM person_site
GROUP BY site_id;

--------------------------------------------------------------------------------
-- Mailing Addresses
--------------------------------------------------------------------------------

-- Mailing addresses
CREATE TABLE addresses (
    address_id serial PRIMARY KEY, -- Address identifier
    address_type text, -- Address type, e.g. shipping or billing
    line1 text NOT NULL, -- Address line 1
    line2 text, -- Address line 2
    line3 text, -- Address line 3
    city text NOT NULL, -- City
    state text NOT NULL, -- State or province
    postalcode text NOT NULL, -- Postal code
    country text NOT NULL -- Country
);

-- Site mailing addresses
CREATE TABLE site_address (
    site_id integer REFERENCES sites, -- Account identifier
    address_id integer REFERENCES addresses, -- Address identifier
    PRIMARY KEY (site_id, address_id)
);
CREATE INDEX site_address_site_id_key ON site_address (site_id);
CREATE INDEX site_address_address_id_key ON site_address (address_id);

CREATE VIEW site_addresses AS
SELECT site_id,
array_to_string(array_accum(address_id), ',') AS address_ids
FROM site_address
GROUP BY site_id;

--------------------------------------------------------------------------------
-- Authentication Keys
--------------------------------------------------------------------------------

-- Valid key types
CREATE TABLE key_types (
    key_type text PRIMARY KEY -- Key type
);
INSERT INTO key_types (key_type) VALUES ('ssh');

-- Authentication keys
CREATE TABLE keys (
    key_id serial PRIMARY KEY, -- Key identifier
    key_type text REFERENCES key_types, -- Key type
    key text NOT NULL, -- Key material
    is_blacklisted boolean NOT NULL DEFAULT false -- Has been blacklisted
);

-- Account authentication key(s)
CREATE TABLE person_key (
    person_id integer REFERENCES persons, -- Account identifier
    key_id integer REFERENCES keys, -- Key identifier
    is_primary boolean NOT NULL DEFAULT false, -- Is the primary key for this account
    PRIMARY KEY (person_id, key_id)
);
CREATE INDEX person_key_person_id_key ON person_key (person_id);
CREATE INDEX person_key_key_id_key ON person_key (key_id);

CREATE VIEW person_keys AS
SELECT person_id,
array_to_string(array_accum(key_id), ',') AS key_ids
FROM person_key
GROUP BY person_id;

--------------------------------------------------------------------------------
-- Account roles
--------------------------------------------------------------------------------

-- Valid account roles
CREATE TABLE roles (
    role_id integer PRIMARY KEY, -- Role identifier
    name text UNIQUE NOT NULL -- Role symbolic name
);
INSERT INTO roles (role_id, name) VALUES (10, 'admin');
INSERT INTO roles (role_id, name) VALUES (20, 'pi');
INSERT INTO roles (role_id, name) VALUES (30, 'user');
INSERT INTO roles (role_id, name) VALUES (40, 'tech');
INSERT INTO roles (role_id, name) VALUES (1000, 'node');
INSERT INTO roles (role_id, name) VALUES (2000, 'anonymous');

CREATE TABLE person_role (
    person_id integer REFERENCES persons, -- Account identifier
    role_id integer REFERENCES roles, -- Role identifier
    PRIMARY KEY (person_id, role_id)
);
CREATE INDEX person_role_person_id_key ON person_role (person_id);

-- Account roles
CREATE VIEW person_roles AS
SELECT person_id,
array_to_string(array_accum(role_id), ',') AS role_ids,
array_to_string(array_accum(roles.name), ',') AS roles
FROM person_role
LEFT JOIN roles USING (role_id)
GROUP BY person_id;

--------------------------------------------------------------------------------
-- Nodes
--------------------------------------------------------------------------------

-- Valid node boot states
CREATE TABLE boot_states (
    boot_state text PRIMARY KEY
);
INSERT INTO boot_states (boot_state) VALUES ('boot');
INSERT INTO boot_states (boot_state) VALUES ('dbg');
INSERT INTO boot_states (boot_state) VALUES ('inst');
INSERT INTO boot_states (boot_state) VALUES ('rins');
INSERT INTO boot_states (boot_state) VALUES ('rcnf');
INSERT INTO boot_states (boot_state) VALUES ('new');

-- Nodes
CREATE TABLE nodes (
    -- Mandatory
    node_id serial PRIMARY KEY, -- Node identifier
    hostname text NOT NULL, -- Node hostname
    site_id integer REFERENCES sites, -- At which site
    boot_state text REFERENCES boot_states, -- Node boot state
    deleted boolean NOT NULL DEFAULT false, -- Is deleted

    -- Optional
    model text, -- Hardware make and model
    boot_nonce text, -- Random nonce updated by Boot Manager
    version text, -- Boot CD version string updated by Boot Manager
    -- XXX Should be key_id integer REFERENCES keys
    ssh_rsa_key text, -- SSH host key updated by Boot Manager
    key text, -- Node key generated by API when configuration file is downloaded
    session text, -- Session key generated by PLC when Boot Manager authenticates

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX nodes_hostname_key ON nodes (hostname);
CREATE INDEX nodes_site_id_key ON nodes (site_id);

-- Nodes at each site
CREATE VIEW site_nodes AS
SELECT site_id,
array_to_string(array_accum(node_id), ',') AS node_ids
FROM nodes
GROUP BY site_id;

--------------------------------------------------------------------------------
-- Node groups
--------------------------------------------------------------------------------

-- Node groups
CREATE TABLE nodegroups (
    nodegroup_id serial PRIMARY KEY, -- Group identifier
    name text UNIQUE NOT NULL, -- Group name
    description text -- Group description
);

-- Node group membership
CREATE TABLE nodegroup_node (
    nodegroup_id integer REFERENCES nodegroups, -- Group identifier
    node_id integer REFERENCES nodes, -- Node identifier
    PRIMARY KEY (nodegroup_id, node_id)
);
CREATE INDEX nodegroup_node_nodegroup_id_key ON nodegroup_node (nodegroup_id);
CREATE INDEX nodegroup_node_node_id_key ON nodegroup_node (node_id);

-- Nodes in each node gruop
CREATE VIEW nodegroup_nodes AS
SELECT nodegroup_id,
array_to_string(array_accum(node_id), ',') AS node_ids
FROM nodegroup_node
GROUP BY nodegroup_id;

-- Node groups that each node is a member of
CREATE VIEW node_nodegroups AS
SELECT node_id,
array_to_string(array_accum(nodegroup_id), ',') AS nodegroup_ids
FROM nodegroup_node
GROUP BY node_id;

--------------------------------------------------------------------------------
-- Node network interfaces
--------------------------------------------------------------------------------

-- Valid network addressing schemes
CREATE TABLE nodenetwork_types (
    type text PRIMARY KEY -- Addressing scheme
);
INSERT INTO nodenetwork_types (type) VALUES ('ipv4');
INSERT INTO nodenetwork_types (type) VALUES ('ipv6');

-- Valid network configuration methods
CREATE TABLE nodenetwork_methods (
    method text PRIMARY KEY -- Configuration method
);
INSERT INTO nodenetwork_methods (method) VALUES ('static');
INSERT INTO nodenetwork_methods (method) VALUES ('dhcp');
INSERT INTO nodenetwork_methods (method) VALUES ('proxy');
INSERT INTO nodenetwork_methods (method) VALUES ('tap');
INSERT INTO nodenetwork_methods (method) VALUES ('ipmi');
INSERT INTO nodenetwork_methods (method) VALUES ('unknown');

-- Node network interfaces
CREATE TABLE nodenetworks (
    -- Mandatory
    nodenetwork_id serial PRIMARY KEY, -- Network interface identifier
    node_id integer REFERENCES nodes, -- Which node
    is_primary boolean NOT NULL DEFAULT false, -- Is the primary interface for this node
    type text REFERENCES nodenetwork_types, -- Addressing scheme
    method text REFERENCES nodenetwork_methods, -- Configuration method

    -- Optional, depending on type and method
    ip text, -- IP address
    mac text, -- MAC address
    gateway text, -- Default gateway address
    network text, -- Network address
    broadcast text, -- Network broadcast address
    netmask text, -- Network mask
    dns1 text, -- Primary DNS server
    dns2 text, -- Secondary DNS server
    bwlimit integer, -- Bandwidth limit in bps
    hostname text -- Hostname of this interface
);
CREATE INDEX nodenetworks_node_id_key ON nodenetworks (node_id);

-- Ordered by primary interface first
CREATE VIEW nodenetworks_ordered AS
SELECT node_id, nodenetwork_id
FROM nodenetworks
ORDER BY is_primary DESC;

-- Network interfaces on each node
CREATE VIEW node_nodenetworks AS
SELECT node_id,
array_to_string(array_accum(nodenetwork_id), ',') AS nodenetwork_ids
FROM nodenetworks_ordered
GROUP BY node_id;

--------------------------------------------------------------------------------
-- Slices
--------------------------------------------------------------------------------

CREATE TABLE slice_instantiations (
    instantiation text PRIMARY KEY
);
INSERT INTO slice_instantiations (instantiation) VALUES ('not-instantiated'); -- Placeholder slice
INSERT INTO slice_instantiations (instantiation) VALUES ('plc-instantiated'); -- Instantiated by Node Manager
INSERT INTO slice_instantiations (instantiation) VALUES ('delegated'); -- Manually instantiated

-- Slices
CREATE TABLE slices (
    slice_id serial PRIMARY KEY, -- Slice identifier
    site_id integer REFERENCES sites, -- Site identifier
    name text NOT NULL, -- Slice name
    instantiation text REFERENCES slice_instantiations DEFAULT 'plc-instantiated', -- Slice state, e.g. plc-instantiated
    url text, -- Project URL
    description text, -- Project description

    max_nodes integer NOT NULL DEFAULT 100, -- Maximum number of nodes that can be assigned to this slice

    creator_person_id integer REFERENCES persons, -- Creator
    created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Creation date
    expires timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP + '2 weeks', -- Expiration date

    is_deleted boolean NOT NULL DEFAULT false
);
CREATE INDEX slices_site_id_key ON slices (site_id);
CREATE INDEX slices_name_key ON slices (name);

-- Slivers
CREATE TABLE slice_node (
    slice_id integer REFERENCES slices, -- Slice identifier
    node_id integer REFERENCES nodes -- Node identifier
);
CREATE INDEX slice_node_slice_id_key ON slice_node (slice_id);
CREATE INDEX slice_node_node_id_key ON slice_node (node_id);

-- Synonym for slice_node
CREATE VIEW slivers AS
SELECT * FROM slice_node;

-- Nodes in each slice
CREATE VIEW slice_nodes AS
SELECT slice_id,
array_to_string(array_accum(node_id), ',') AS node_ids
FROM slice_node
GROUP BY slice_id;

-- Slices on each node
CREATE VIEW node_slices AS
SELECT node_id,
array_to_string(array_accum(slice_id), ',') AS slice_ids
FROM slice_node
GROUP BY node_id;

-- Slices at each site
CREATE VIEW site_slices AS
SELECT site_id,
array_to_string(array_accum(slice_id), ',') AS slice_ids
FROM slices
GROUP BY site_id;

-- Slice membership
CREATE TABLE slice_person (
    slice_id integer REFERENCES slices, -- Slice identifier
    person_id integer REFERENCES persons, -- Account identifier
    PRIMARY KEY (slice_id, person_id)
);
CREATE INDEX slice_person_slice_id_key ON slice_person (slice_id);
CREATE INDEX slice_person_person_id_key ON slice_person (person_id);

-- Members of the slice
CREATE VIEW slice_persons AS
SELECT slice_id,
array_to_string(array_accum(person_id), ',') AS person_ids
FROM slice_person
GROUP BY slice_id;

-- Slices of which each person is a member
CREATE VIEW person_slices AS
SELECT person_id,
array_to_string(array_accum(slice_id), ',') AS slice_ids
FROM slice_person
GROUP BY person_id;

--------------------------------------------------------------------------------
-- Slice attributes
--------------------------------------------------------------------------------

CREATE TABLE attributes (
    attribute_id serial PRIMARY KEY, -- Attribute identifier
    name text UNIQUE NOT NULL, -- Attribute name
    description text, -- Attribute description
    min_role_id integer REFERENCES roles -- Minimum (least powerful) role that can set or change this attribute
);

-- Slice/sliver attributes
CREATE TABLE slice_attribute (
    slice_id integer REFERENCES slices, -- Slice identifier
    attribute_id integer REFERENCES attributes, -- Attribute identifier
    node_id integer, -- Sliver attribute if set
    value text,
    PRIMARY KEY (slice_id, attribute_id, node_id)
);
CREATE INDEX slice_attribute_slice_id_key ON slice_attribute (slice_id);
CREATE INDEX slice_attribute_node_id_key ON slice_attribute (node_id);

CREATE VIEW slice_attributes AS
SELECT slice_id,
array_to_string(array_accum(attribute_id), ',') AS attribute_ids
FROM slice_attribute
WHERE node_id IS NULL
GROUP BY slice_id;

-- No sliver_attributes view since it by definition requires a conditional on node_id

--------------------------------------------------------------------------------
-- Useful views
--------------------------------------------------------------------------------

CREATE VIEW view_persons AS
SELECT
persons.person_id,
persons.email,
persons.first_name,
persons.last_name,
persons.deleted,
persons.enabled,
persons.password,
persons.verification_key,
persons.verification_expires,
persons.title,
persons.phone,
persons.url,
persons.bio,
CAST(date_part('epoch', persons.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', persons.last_updated) AS bigint) AS last_updated,
person_roles.role_ids, person_roles.roles,
person_sites.site_ids,
person_keys.key_ids,
person_slices.slice_ids
FROM persons
LEFT JOIN person_roles USING (person_id)
LEFT JOIN person_sites USING (person_id)
LEFT JOIN person_keys USING (person_id)
LEFT JOIN person_slices USING (person_id);

CREATE VIEW view_nodes AS
SELECT
nodes.node_id,
nodes.hostname,
nodes.site_id,
nodes.boot_state,
nodes.deleted,
nodes.model,
nodes.boot_nonce,
nodes.version,
nodes.ssh_rsa_key,
nodes.key,
nodes.session,
CAST(date_part('epoch', nodes.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', nodes.last_updated) AS bigint) AS last_updated,
node_nodenetworks.nodenetwork_ids,
node_nodegroups.nodegroup_ids,
node_slices.slice_ids
FROM nodes
LEFT JOIN node_nodenetworks USING (node_id)
LEFT JOIN node_nodegroups USING (node_id)
LEFT JOIN node_slices USING (node_id);

CREATE VIEW view_nodegroups AS
SELECT
nodegroups.nodegroup_id,
nodegroups.name,
nodegroups.description,
nodegroup_nodes.node_ids
FROM nodegroups
LEFT JOIN nodegroup_nodes USING (nodegroup_id);

CREATE VIEW view_sites AS
SELECT
sites.site_id,
sites.login_base,
sites.name,
sites.abbreviated_name,
sites.deleted,
sites.is_public,
sites.max_slices,
sites.max_slivers,
sites.latitude,
sites.longitude,
sites.url,
CAST(date_part('epoch', sites.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', sites.last_updated) AS bigint) AS last_updated,
site_persons.person_ids,
site_nodes.node_ids,
site_addresses.address_ids,
site_slices.slice_ids
FROM sites
LEFT JOIN site_persons USING (site_id)
LEFT JOIN site_nodes USING (site_id)
LEFT JOIN site_addresses USING (site_id)
LEFT JOIN site_slices USING (site_id);

CREATE VIEW view_addresses AS
SELECT
addresses.address_id,
addresses.address_type,
addresses.line1,
addresses.line2,
addresses.line3,
addresses.city,
addresses.state,
addresses.postalcode,
addresses.country,
site_address.site_id
FROM addresses
LEFT JOIN site_address USING (address_id);

CREATE VIEW view_slices AS
SELECT
slices.slice_id,
slices.site_id,
slices.name,
slices.instantiation,
slices.url,
slices.description,
slices.max_nodes,
slices.creator_person_id,
slices.is_deleted,
CAST(date_part('epoch', slices.created) AS bigint) AS created,
CAST(date_part('epoch', slices.expires) AS bigint) AS expires,
slice_nodes.node_ids,
slice_persons.person_ids,
slice_attributes.attribute_ids
FROM slices
LEFT JOIN slice_nodes USING (slice_id)
LEFT JOIN slice_persons USING (slice_id)
LEFT JOIN slice_attributes USING (slice_id);

--------------------------------------------------------------------------------
-- Built-in maintenance account and default site
--------------------------------------------------------------------------------

INSERT INTO persons
(first_name, last_name, email, password, enabled)
VALUES
('Maintenance', 'Account', 'maint@localhost.localdomain', 'nopass', true);

INSERT INTO person_role (person_id, role_id) VALUES (1, 10);
INSERT INTO person_role (person_id, role_id) VALUES (1, 20);
INSERT INTO person_role (person_id, role_id) VALUES (1, 30);
INSERT INTO person_role (person_id, role_id) VALUES (1, 40);

INSERT INTO sites
(login_base, name, abbreviated_name, max_slices)
VALUES
('pl', 'PlanetLab Central', 'PLC', 100);

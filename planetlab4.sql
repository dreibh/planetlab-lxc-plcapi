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
-- $Id$
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
    email text UNIQUE NOT NULL, -- E-mail address
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

--------------------------------------------------------------------------------
-- Sites
--------------------------------------------------------------------------------

-- Sites
CREATE TABLE sites (
    -- Mandatory
    site_id serial PRIMARY KEY, -- Site identifier
    login_base text UNIQUE NOT NULL, -- Site slice prefix
    name text NOT NULL, -- Site name
    abbreviated_name text NOT NULL, -- Site abbreviated name
    deleted boolean NOT NULL DEFAULT false, -- Has been deleted
    is_public boolean NOT NULL DEFAULT true, -- Shows up in public lists
    max_slices integer NOT NULL DEFAULT 0, -- Maximum number of slices

    -- XXX Sites should have an address
    -- address_id REFERENCES addresses,

    -- Optional
    latitude real,
    longitude real,
    url text,

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Account site membership
CREATE TABLE person_site (
    person_id integer REFERENCES persons, -- Account identifier
    site_id integer REFERENCES sites, -- Site identifier
    is_primary boolean NOT NULL DEFAULT false, -- Is the primary site for this account
    PRIMARY KEY (person_id, site_id)
);

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

-- Valid mailing address types
CREATE TABLE address_types (
    address_type_id serial PRIMARY KEY, -- Address type identifier
    address_type text UNIQUE NOT NULL -- Address type
);
INSERT INTO address_types (address_type) VALUES ('Personal');
INSERT INTO address_types (address_type) VALUES ('Shipping');
INSERT INTO address_types (address_type) VALUES ('Site');

-- Mailing addresses
CREATE TABLE addresses (
    address_id serial PRIMARY KEY, -- Address identifier
    line1 text NOT NULL, -- Address line 1
    line2 text, -- Address line 2
    line3 text, -- Address line 3
    city text NOT NULL, -- City
    state text NOT NULL, -- State or province
    postalcode text NOT NULL, -- Postal code
    country text NOT NULL -- Country
);

-- Each address can be multiple types
CREATE TABLE address_address_type (
    address_id integer REFERENCES addresses,
    address_type_id integer REFERENCES address_types,
    PRIMARY KEY (address_id, address_type_id)
);

-- Types of each address
CREATE VIEW address_address_types AS
SELECT address_id,
array_to_string(array_accum(address_type_id), ',') AS address_type_ids,
array_to_string(array_accum(address_type), ',') AS address_types
FROM address_address_type
LEFT JOIN address_types USING (address_type_id)
GROUP BY address_id;

CREATE TABLE person_address (
    person_id integer REFERENCES persons, -- Account identifier
    address_id integer REFERENCES addresses, -- Address identifier
    PRIMARY KEY (person_id, address_id)
);

-- Account mailing addresses
CREATE VIEW person_addresses AS
SELECT person_id,
array_to_string(array_accum(address_id), ',') AS address_ids
FROM person_address
GROUP BY person_id;

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
    hostname text UNIQUE NOT NULL, -- Node hostname
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

-- Network interfaces on each node
CREATE VIEW node_nodenetworks AS
SELECT node_id,
array_to_string(array_accum(nodenetwork_id), ',') AS nodenetwork_ids
FROM nodenetworks
GROUP BY node_id;

--------------------------------------------------------------------------------
-- Useful views
--------------------------------------------------------------------------------

CREATE VIEW view_persons AS
SELECT persons.*,
person_roles.role_ids,
person_roles.roles,
person_sites.site_ids,
person_addresses.address_ids,
person_keys.key_ids
FROM persons
LEFT JOIN person_roles USING (person_id)
LEFT JOIN person_sites USING (person_id)
LEFT JOIN person_addresses USING (person_id)
LEFT JOIN person_keys USING (person_id);

CREATE VIEW view_addresses AS
SELECT addresses.*,
address_address_types.address_type_ids,
address_address_types.address_types
FROM addresses
LEFT JOIN address_address_types USING (address_id);

CREATE VIEW view_nodes AS
SELECT nodes.*,
node_nodenetworks.nodenetwork_ids,
node_nodegroups.nodegroup_ids
FROM nodes
LEFT JOIN node_nodenetworks USING (node_id)
LEFT JOIN node_nodegroups USING (node_id);

CREATE VIEW view_nodegroups AS
SELECT nodegroups.*,
nodegroup_nodes.node_ids
FROM nodegroups
LEFT JOIN nodegroup_nodes USING (nodegroup_id);

CREATE VIEW view_sites AS
SELECT sites.*,
site_persons.person_ids,
site_nodes.node_ids
FROM sites
LEFT JOIN site_persons USING (site_id)
LEFT JOIN site_nodes USING (site_id);

--------------------------------------------------------------------------------
-- Built-in maintenance account and default site
--------------------------------------------------------------------------------

INSERT INTO persons
(first_name, last_name, email, password, enabled)
VALUES
('Maintenance', 'Account', 'maint@planet-lab.org', 'nopass', true);

INSERT INTO person_role (person_id, role_id) VALUES (1, 10);
INSERT INTO person_role (person_id, role_id) VALUES (1, 20);
INSERT INTO person_role (person_id, role_id) VALUES (1, 30);
INSERT INTO person_role (person_id, role_id) VALUES (1, 40);

INSERT INTO sites
(login_base, name, abbreviated_name, max_slices)
VALUES
('pl', 'PlanetLab Central', 'PLC', 100);

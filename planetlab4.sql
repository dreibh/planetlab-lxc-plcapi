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
-- $Id: planetlab4.sql,v 1.25 2006/10/31 21:45:45 mlhuang Exp $
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
) WITH OIDS;
CREATE INDEX persons_email_idx ON persons (email) WHERE deleted IS false;

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
) WITH OIDS;
CREATE INDEX sites_login_base_idx ON sites (login_base) WHERE deleted IS false;

-- Account site membership
CREATE TABLE person_site (
    person_id integer REFERENCES persons NOT NULL, -- Account identifier
    site_id integer REFERENCES sites NOT NULL, -- Site identifier
    is_primary boolean NOT NULL DEFAULT false, -- Is the primary site for this account
    PRIMARY KEY (person_id, site_id)
);
CREATE INDEX person_site_person_id_idx ON person_site (person_id);
CREATE INDEX person_site_site_id_idx ON person_site (site_id);

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

CREATE TABLE address_types (
    address_type_id serial PRIMARY KEY, -- Address type identifier
    name text UNIQUE NOT NULL, -- Address type
    description text -- Address type description
) WITH OIDS;

INSERT INTO address_types (name) VALUES ('Personal');
INSERT INTO address_types (name) VALUES ('Shipping');
-- XXX Used to be Site
INSERT INTO address_types (name) VALUES ('Billing');

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
) WITH OIDS;

-- Each mailing address can be one of several types
CREATE TABLE address_address_type (
    address_id integer REFERENCES addresses NOT NULL, -- Address identifier
    address_type_id integer REFERENCES address_types NOT NULL, -- Address type
    PRIMARY KEY (address_id, address_type_id)
) WITH OIDS;
CREATE INDEX address_address_type_address_id_idx ON address_address_type (address_id);
CREATE INDEX address_address_type_address_type_id_idx ON address_address_type (address_type_id);

CREATE VIEW address_address_types AS
SELECT address_id,
array_to_string(array_accum(address_type_id), ',') AS address_type_ids,
array_to_string(array_accum(address_types.name), ',') AS address_types
FROM address_address_type
LEFT JOIN address_types USING (address_type_id)
GROUP BY address_id;

CREATE TABLE site_address (
    site_id integer REFERENCES sites NOT NULL, -- Site identifier
    address_id integer REFERENCES addresses NOT NULL, -- Address identifier
    PRIMARY KEY (site_id, address_id)
) WITH OIDS;
CREATE INDEX site_address_site_id_idx ON site_address (site_id);
CREATE INDEX site_address_address_id_idx ON site_address (address_id);

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
) WITH OIDS;
INSERT INTO key_types (key_type) VALUES ('ssh');

-- Authentication keys
CREATE TABLE keys (
    key_id serial PRIMARY KEY, -- Key identifier
    key_type text REFERENCES key_types NOT NULL, -- Key type
    key text NOT NULL, -- Key material
    is_blacklisted boolean NOT NULL DEFAULT false -- Has been blacklisted
) WITH OIDS;

-- Account authentication key(s)
CREATE TABLE person_key (
    person_id integer REFERENCES persons NOT NULL, -- Account identifier
    key_id integer REFERENCES keys NOT NULL, -- Key identifier
    PRIMARY KEY (person_id, key_id)
) WITH OIDS;
CREATE INDEX person_key_person_id_idx ON person_key (person_id);
CREATE INDEX person_key_key_id_idx ON person_key (key_id);

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
) WITH OIDS;
INSERT INTO roles (role_id, name) VALUES (10, 'admin');
INSERT INTO roles (role_id, name) VALUES (20, 'pi');
INSERT INTO roles (role_id, name) VALUES (30, 'user');
INSERT INTO roles (role_id, name) VALUES (40, 'tech');
INSERT INTO roles (role_id, name) VALUES (1000, 'node');
INSERT INTO roles (role_id, name) VALUES (2000, 'anonymous');

CREATE TABLE person_role (
    person_id integer REFERENCES persons NOT NULL, -- Account identifier
    role_id integer REFERENCES roles NOT NULL, -- Role identifier
    PRIMARY KEY (person_id, role_id)
) WITH OIDS;
CREATE INDEX person_role_person_id_idx ON person_role (person_id);

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
) WITH OIDS;
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
    site_id integer REFERENCES sites NOT NULL, -- At which site
    boot_state text REFERENCES boot_states NOT NULL DEFAULT 'inst', -- Node boot state
    deleted boolean NOT NULL DEFAULT false, -- Is deleted

    -- Optional
    model text, -- Hardware make and model
    boot_nonce text, -- Random nonce updated by Boot Manager
    version text, -- Boot CD version string updated by Boot Manager
    -- XXX Should be key_id integer REFERENCES keys
    ssh_rsa_key text, -- SSH host key updated by Boot Manager
    key text, -- Node key generated by API when configuration file is downloaded

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
) WITH OIDS;
CREATE INDEX nodes_hostname_idx ON nodes (hostname) WHERE deleted IS false;
CREATE INDEX nodes_site_id_idx ON nodes (site_id) WHERE deleted IS false;

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
) WITH OIDS;

-- Node group membership
CREATE TABLE nodegroup_node (
    nodegroup_id integer REFERENCES nodegroups NOT NULL, -- Group identifier
    node_id integer REFERENCES nodes NOT NULL, -- Node identifier
    PRIMARY KEY (nodegroup_id, node_id)
) WITH OIDS;
CREATE INDEX nodegroup_node_nodegroup_id_idx ON nodegroup_node (nodegroup_id);
CREATE INDEX nodegroup_node_node_id_idx ON nodegroup_node (node_id);

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
-- Node configuration files
--------------------------------------------------------------------------------

CREATE TABLE conf_files (
    conf_file_id serial PRIMARY KEY, -- Configuration file identifier
    enabled bool NOT NULL DEFAULT true, -- Configuration file is active
    source text NOT NULL, -- Relative path on the boot server where file can be downloaded
    dest text NOT NULL, -- Absolute path where file should be installed
    file_permissions text NOT NULL DEFAULT '0644', -- chmod(1) permissions
    file_owner text NOT NULL DEFAULT 'root', -- chown(1) owner
    file_group text NOT NULL DEFAULT 'root', -- chgrp(1) owner
    preinstall_cmd text, -- Shell command to execute prior to installing
    postinstall_cmd text, -- Shell command to execute after installing
    error_cmd text, -- Shell command to execute if any error occurs
    ignore_cmd_errors bool NOT NULL DEFAULT false, -- Install file anyway even if an error occurs
    always_update bool NOT NULL DEFAULT false -- Always attempt to install file even if unchanged
);

CREATE TABLE conf_file_node (
    conf_file_id integer REFERENCES conf_files NOT NULL, -- Configuration file identifier
    node_id integer REFERENCES nodes NOT NULL, -- Node identifier
    PRIMARY KEY (conf_file_id, node_id)
);
CREATE INDEX conf_file_node_conf_file_id_idx ON conf_file_node (conf_file_id);
CREATE INDEX conf_file_node_node_id_idx ON conf_file_node (node_id);

-- Nodes linked to each configuration file
CREATE VIEW conf_file_nodes AS
SELECT conf_file_id,
array_to_string(array_accum(node_id), ',') AS node_ids
FROM conf_file_node
GROUP BY conf_file_id;

-- Configuration files linked to each node
CREATE VIEW node_conf_files AS
SELECT node_id,
array_to_string(array_accum(conf_file_id), ',') AS conf_file_ids
FROM conf_file_node
GROUP BY node_id;

CREATE TABLE conf_file_nodegroup (
    conf_file_id integer REFERENCES conf_files NOT NULL, -- Configuration file identifier
    nodegroup_id integer REFERENCES nodegroups NOT NULL, -- Node group identifier
    PRIMARY KEY (conf_file_id, nodegroup_id)
);
CREATE INDEX conf_file_nodegroup_conf_file_id_idx ON conf_file_nodegroup (conf_file_id);
CREATE INDEX conf_file_nodegroup_nodegroup_id_idx ON conf_file_nodegroup (nodegroup_id);

-- Node groups linked to each configuration file
CREATE VIEW conf_file_nodegroups AS
SELECT conf_file_id,
array_to_string(array_accum(nodegroup_id), ',') AS nodegroup_ids
FROM conf_file_nodegroup
GROUP BY conf_file_id;

-- Configuration files linked to each node group
CREATE VIEW nodegroup_conf_files AS
SELECT nodegroup_id,
array_to_string(array_accum(conf_file_id), ',') AS conf_file_ids
FROM conf_file_nodegroup
GROUP BY nodegroup_id;

--------------------------------------------------------------------------------
-- Node network interfaces
--------------------------------------------------------------------------------

-- Valid network addressing schemes
CREATE TABLE network_types (
    type text PRIMARY KEY -- Addressing scheme
) WITH OIDS;
INSERT INTO network_types (type) VALUES ('ipv4');

-- Valid network configuration methods
CREATE TABLE network_methods (
    method text PRIMARY KEY -- Configuration method
) WITH OIDS;
INSERT INTO network_methods (method) VALUES ('static');
INSERT INTO network_methods (method) VALUES ('dhcp');
INSERT INTO network_methods (method) VALUES ('proxy');
INSERT INTO network_methods (method) VALUES ('tap');
INSERT INTO network_methods (method) VALUES ('ipmi');
INSERT INTO network_methods (method) VALUES ('unknown');

-- Node network interfaces
CREATE TABLE nodenetworks (
    -- Mandatory
    nodenetwork_id serial PRIMARY KEY, -- Network interface identifier
    node_id integer REFERENCES nodes NOT NULL, -- Which node
    is_primary boolean NOT NULL DEFAULT false, -- Is the primary interface for this node
    type text REFERENCES network_types NOT NULL, -- Addressing scheme
    method text REFERENCES network_methods NOT NULL, -- Configuration method

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
) WITH OIDS;
CREATE INDEX nodenetworks_node_id_idx ON nodenetworks (node_id);

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
-- Power control units (PCUs)
--------------------------------------------------------------------------------

CREATE TABLE pcus (
    -- Mandatory
    pcu_id serial PRIMARY KEY, -- PCU identifier
    site_id integer REFERENCES sites NOT NULL, -- Site identifier
    hostname text, -- Hostname, not necessarily unique (multiple logical sites could use the same PCU)
    ip text NOT NULL, -- IP, not necessarily unique

    -- Optional
    protocol text, -- Protocol, e.g. ssh or https or telnet
    username text, -- Username, if applicable
    "password" text, -- Password, if applicable
    model text, -- Model, e.g. BayTech or iPal
    notes text -- Random notes
) WITH OIDS;
CREATE INDEX pcus_site_id_idx ON pcus (site_id);

CREATE VIEW site_pcus AS
SELECT site_id,
array_to_string(array_accum(pcu_id), ',') AS pcu_ids
FROM pcus
GROUP BY site_id;

CREATE TABLE pcu_node (
    pcu_id integer REFERENCES pcus NOT NULL, -- PCU identifier
    node_id integer REFERENCES nodes NOT NULL, -- Node identifier
    port integer NOT NULL, -- Port number
    PRIMARY KEY (pcu_id, node_id), -- The same node cannot be controlled by different ports
    UNIQUE (pcu_id, port) -- The same port cannot control multiple nodes
);
CREATE INDEX pcu_node_pcu_id_idx ON pcu_node (pcu_id);
CREATE INDEX pcu_node_node_id_idx ON pcu_node (node_id);

CREATE VIEW node_pcus AS
SELECT node_id,
array_to_string(array_accum(pcu_id), ',') AS pcu_ids,
array_to_string(array_accum(port), ',') AS ports
FROM pcu_node
GROUP BY node_id;

CREATE VIEW pcu_nodes AS
SELECT pcu_id,
array_to_string(array_accum(node_id), ',') AS node_ids,
array_to_string(array_accum(port), ',') AS ports
FROM pcu_node
GROUP BY pcu_id;

--------------------------------------------------------------------------------
-- Slices
--------------------------------------------------------------------------------

CREATE TABLE slice_instantiations (
    instantiation text PRIMARY KEY
) WITH OIDS;
INSERT INTO slice_instantiations (instantiation) VALUES ('not-instantiated'); -- Placeholder slice
INSERT INTO slice_instantiations (instantiation) VALUES ('plc-instantiated'); -- Instantiated by Node Manager
INSERT INTO slice_instantiations (instantiation) VALUES ('delegated'); -- Manually instantiated

-- Slices
CREATE TABLE slices (
    slice_id serial PRIMARY KEY, -- Slice identifier
    site_id integer REFERENCES sites NOT NULL, -- Site identifier
    name text NOT NULL, -- Slice name
    instantiation text REFERENCES slice_instantiations NOT NULL DEFAULT 'plc-instantiated', -- Slice state, e.g. plc-instantiated
    url text, -- Project URL
    description text, -- Project description

    max_nodes integer NOT NULL DEFAULT 100, -- Maximum number of nodes that can be assigned to this slice

    creator_person_id integer REFERENCES persons NOT NULL, -- Creator
    created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Creation date
    expires timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP + '2 weeks', -- Expiration date

    is_deleted boolean NOT NULL DEFAULT false
) WITH OIDS;
CREATE INDEX slices_site_id_idx ON slices (site_id) WHERE is_deleted IS false;
CREATE INDEX slices_name_idx ON slices (name) WHERE is_deleted IS false;

-- Slivers
CREATE TABLE slice_node (
    slice_id integer REFERENCES slices NOT NULL, -- Slice identifier
    node_id integer REFERENCES nodes NOT NULL, -- Node identifier
    PRIMARY KEY (slice_id, node_id)
) WITH OIDS;
CREATE INDEX slice_node_slice_id_idx ON slice_node (slice_id);
CREATE INDEX slice_node_node_id_idx ON slice_node (node_id);

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
    slice_id integer REFERENCES slices NOT NULL, -- Slice identifier
    person_id integer REFERENCES persons NOT NULL, -- Account identifier
    PRIMARY KEY (slice_id, person_id)
) WITH OIDS;
CREATE INDEX slice_person_slice_id_idx ON slice_person (slice_id);
CREATE INDEX slice_person_person_id_idx ON slice_person (person_id);

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

-- Slice attribute types
CREATE TABLE slice_attribute_types (
    attribute_type_id serial PRIMARY KEY, -- Attribute type identifier
    name text UNIQUE NOT NULL, -- Attribute name
    description text, -- Attribute description
    min_role_id integer REFERENCES roles DEFAULT 10 -- If set, minimum (least powerful) role that can set or change this attribute
) WITH OIDS;

-- Slice/sliver attributes
CREATE TABLE slice_attribute (
    slice_attribute_id serial PRIMARY KEY, -- Slice attribute identifier
    slice_id integer REFERENCES slices NOT NULL, -- Slice identifier
    node_id integer REFERENCES nodes, -- Sliver attribute if set
    attribute_type_id integer REFERENCES slice_attribute_types NOT NULL, -- Attribute type identifier
    value text
) WITH OIDS;
CREATE INDEX slice_attribute_slice_id_idx ON slice_attribute (slice_id);
CREATE INDEX slice_attribute_node_id_idx ON slice_attribute (node_id);

CREATE VIEW slice_attributes AS
SELECT slice_id,
array_to_string(array_accum(slice_attribute_id), ',') AS slice_attribute_ids
FROM slice_attribute
GROUP BY slice_id;

--------------------------------------------------------------------------------
-- Authenticated sessions
--------------------------------------------------------------------------------

-- Authenticated sessions
CREATE TABLE sessions (
    session_id text PRIMARY KEY, -- Session identifier
    expires timestamp without time zone
) WITH OIDS;

-- People can have multiple sessions
CREATE TABLE person_session (
    person_id integer REFERENCES persons NOT NULL, -- Account identifier
    session_id text REFERENCES sessions NOT NULL, -- Session identifier
    PRIMARY KEY (person_id, session_id),
    UNIQUE (session_id) -- Sessions are unique
) WITH OIDS;
CREATE INDEX person_session_person_id_idx ON person_session (person_id);

-- Nodes can have only one session
CREATE TABLE node_session (
    node_id integer REFERENCES nodes NOT NULL, -- Node identifier
    session_id text REFERENCES sessions NOT NULL, -- Session identifier
    UNIQUE (node_id), -- Nodes can have only one session
    UNIQUE (session_id) -- Sessions are unique
) WITH OIDS;

--------------------------------------------------------------------------------
-- Message templates
--------------------------------------------------------------------------------

CREATE TABLE messages (
    message_id text PRIMARY KEY, -- Message name
    template text, -- Message template
    enabled bool NOT NULL DEFAULT true -- Whether message is enabled
) WITH OIDS;

--------------------------------------------------------------------------------
-- Events
--------------------------------------------------------------------------------

-- Event types
CREATE TABLE event_types (
    event_type text PRIMARY KEY -- Event type
) WITH OIDS;
INSERT INTO event_types (event_type) VALUES ('Add');
INSERT INTO event_types (event_type) VALUES ('AddTo');
INSERT INTO event_types (event_type) VALUES ('Get');
INSERT INTO event_types (event_type) VALUES ('Update');
INSERT INTO event_types (event_type) VALUES ('Delete');
INSERT INTO event_types (event_type) VALUES ('DeleteFrom');
INSERT INTO event_types (event_type) VALUES ('Unknown');

-- Object types
CREATE TABLE object_types (
    object_type text PRIMARY KEY -- Object type 
) WITH OIDS;
INSERT INTO object_types (object_type) VALUES ('AddressType');
INSERT INTO object_types (object_type) VALUES ('Address');
INSERT INTO object_types (object_type) VALUES ('BootState');
INSERT INTO object_types (object_type) VALUES ('ConfFile');
INSERT INTO object_types (object_type) VALUES ('KeyType');
INSERT INTO object_types (object_type) VALUES ('Key');
INSERT INTO object_types (object_type) VALUES ('NetworkMethod');
INSERT INTO object_types (object_type) VALUES ('NetworkType');
INSERT INTO object_types (object_type) VALUES ('Network');
INSERT INTO object_types (object_type) VALUES ('NodeGroup');
INSERT INTO object_types (object_type) VALUES ('NodeNetwork');
INSERT INTO object_types (object_type) VALUES ('Node');
INSERT INTO object_types (object_type) VALUES ('PCU');
INSERT INTO object_types (object_type) VALUES ('Person');
INSERT INTO object_types (object_type) VALUES ('Role');
INSERT INTO object_types (object_type) VALUES ('Session');
INSERT INTO object_types (object_type) VALUES ('Site');
INSERT INTO object_types (object_type) VALUES ('SliceAttributeType');
INSERT INTO object_types (object_type) VALUES ('SliceAttribute');
INSERT INTO object_types (object_type) VALUES ('Slice');
INSERT INTO object_types (object_type) VALUES ('Unknown');

-- Events
CREATE TABLE events (
    event_id serial PRIMARY KEY,  -- Event identifier
    person_id integer REFERENCES persons, -- Person responsible for event, if any
    node_id integer REFERENCES nodes, -- Node responsible for event, if any
    event_type text REFERENCES event_types NOT NULL DEFAULT 'Unknown', -- Event type 
    object_type text REFERENCES object_types NOT NULL DEFAULT 'Unknown', -- Object type associated with event
    fault_code integer NOT NULL DEFAULT 0, -- Did this event result in error
    call text NOT NULL, -- Call responsible for this event
    runtime float, -- Event run time
    time timestamp without time zone  NOT NULL DEFAULT CURRENT_TIMESTAMP -- Event timestamp
) WITH OIDS;

-- Event objects
CREATE TABLE event_object (
    event_id integer REFERENCES events NOT NULL, -- Event identifier
    object_id integer NOT NULL -- Object identifier
) WITH OIDS;
CREATE INDEX event_object_event_id_idx ON event_object (event_id);
CREATE INDEX event_object_object_id_idx ON event_object (object_id);

CREATE VIEW event_objects AS
SELECT event_id,
array_to_string(array_accum(object_id), ',') AS object_ids
FROM event_object
GROUP BY event_id;

--------------------------------------------------------------------------------
-- Useful views
--------------------------------------------------------------------------------

CREATE VIEW view_events AS
SELECT
events.event_id,
events.person_id,
events.node_id,
event_objects.object_ids,
events.event_type,
events.object_type,
events.fault_code,
events.call,
events.runtime,
CAST(date_part('epoch', events.time) AS bigint) AS time
FROM events
LEFT JOIN event_objects USING (event_id);

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
CAST(date_part('epoch', nodes.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', nodes.last_updated) AS bigint) AS last_updated,
node_nodenetworks.nodenetwork_ids,
node_nodegroups.nodegroup_ids,
node_slices.slice_ids,
node_pcus.pcu_ids,
node_pcus.ports,
node_conf_files.conf_file_ids,
node_session.session_id AS session
FROM nodes
LEFT JOIN node_nodenetworks USING (node_id)
LEFT JOIN node_nodegroups USING (node_id)
LEFT JOIN node_slices USING (node_id)
LEFT JOIN node_pcus USING (node_id)
LEFT JOIN node_conf_files USING (node_id)
LEFT JOIN node_session USING (node_id);

CREATE VIEW view_nodegroups AS
SELECT
nodegroups.nodegroup_id,
nodegroups.name,
nodegroups.description,
nodegroup_nodes.node_ids,
nodegroup_conf_files.conf_file_ids
FROM nodegroups
LEFT JOIN nodegroup_nodes USING (nodegroup_id)
LEFT JOIN nodegroup_conf_files USING (nodegroup_id);

CREATE VIEW view_conf_files AS
SELECT
conf_files.conf_file_id,
conf_files.enabled,
conf_files.source,
conf_files.dest,
conf_files.file_permissions,
conf_files.file_owner,
conf_files.file_group,
conf_files.preinstall_cmd,
conf_files.postinstall_cmd,
conf_files.error_cmd,
conf_files.ignore_cmd_errors,
conf_files.always_update,
conf_file_nodes.node_ids,
conf_file_nodegroups.nodegroup_ids
FROM conf_files
LEFT JOIN conf_file_nodes USING (conf_file_id)
LEFT JOIN conf_file_nodegroups USING (conf_file_id);

CREATE VIEW view_pcus AS
SELECT
pcus.pcu_id,
pcus.site_id,
pcus.hostname,
pcus.ip,
pcus.protocol,
pcus.username,
pcus.password,
pcus.model,
pcus.notes,
pcu_nodes.node_ids,
pcu_nodes.ports
FROM pcus
LEFT JOIN pcu_nodes USING (pcu_id);

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
site_slices.slice_ids,
site_pcus.pcu_ids
FROM sites
LEFT JOIN site_persons USING (site_id)
LEFT JOIN site_nodes USING (site_id)
LEFT JOIN site_addresses USING (site_id)
LEFT JOIN site_slices USING (site_id)
LEFT JOIN site_pcus USING (site_id);

CREATE VIEW view_addresses AS
SELECT
addresses.address_id,
addresses.line1,
addresses.line2,
addresses.line3,
addresses.city,
addresses.state,
addresses.postalcode,
addresses.country,
address_address_types.address_type_ids,
address_address_types.address_types
FROM addresses
LEFT JOIN address_address_types USING (address_id);

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
slice_attributes.slice_attribute_ids
FROM slices
LEFT JOIN slice_nodes USING (slice_id)
LEFT JOIN slice_persons USING (slice_id)
LEFT JOIN slice_attributes USING (slice_id);

CREATE VIEW view_slice_attributes AS
SELECT
slice_attribute.slice_attribute_id,
slice_attribute.slice_id,
slice_attribute.node_id,
slice_attribute_types.attribute_type_id,
slice_attribute_types.name,
slice_attribute_types.description,
slice_attribute_types.min_role_id,
slice_attribute.value
FROM slice_attribute
INNER JOIN slice_attribute_types USING (attribute_type_id);

CREATE VIEW view_sessions AS
SELECT
sessions.session_id,
CAST(date_part('epoch', sessions.expires) AS bigint) AS expires,
person_session.person_id,
node_session.node_id
FROM sessions
LEFT JOIN person_session USING (session_id)
LEFT JOIN node_session USING (session_id);

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

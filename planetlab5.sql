--
-- PlanetLab Central database schema
-- Version 5, PostgreSQL
--
-- Aaron Klingaman <alk@cs.princeton.edu>
-- Reid Moran <rmoran@cs.princeton.edu>
-- Mark Huang <mlhuang@cs.princeton.edu>
-- Tony Mack <tmack@cs.princeton.edu>
-- Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr>
--
-- Copyright (C) 2006 The Trustees of Princeton University
--
-- NOTE: this file was first created for version 4.3, the filename might be confusing
--

SET client_encoding = 'UNICODE';

--------------------------------------------------------------------------------
-- Version
--------------------------------------------------------------------------------

-- Database version
CREATE TABLE plc_db_version (
    version integer NOT NULL,
    subversion integer NOT NULL DEFAULT 0
) WITH OIDS;

-- the migration scripts do not use the major 'version' number
-- so 5.0 sets subversion at 100
-- in case your database misses the site and persons tags feature, 
-- you might wish to first upgrade to 4.3-rc16 before moving to some 5.0
-- or run the up script here
-- http://svn.planet-lab.org/svn/PLCAPI/branches/4.3/migrations/

INSERT INTO plc_db_version (version, subversion) VALUES (5, 100);

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
-- Roles
--------------------------------------------------------------------------------

-- Valid account roles
CREATE TABLE roles (
    role_id integer PRIMARY KEY,			-- Role identifier
    name text UNIQUE NOT NULL				-- Role symbolic name
) WITH OIDS;
INSERT INTO roles (role_id, name) VALUES (10, 'admin');
INSERT INTO roles (role_id, name) VALUES (20, 'pi');
INSERT INTO roles (role_id, name) VALUES (30, 'user');
INSERT INTO roles (role_id, name) VALUES (40, 'tech');

--------------------------------------------------------------------------------
-- The building block for attaching tags
--------------------------------------------------------------------------------
CREATE TABLE tag_types (

    tag_type_id serial PRIMARY KEY,			-- ID
    tagname text UNIQUE NOT NULL,			-- Tag Name
    description text,					-- Optional Description
-- this is deprecated -- see migrations/104*
-- starting with subversion 104, a tag type has a SET OF roles attached to it
    min_role_id integer REFERENCES roles DEFAULT 10,	-- set minimal role required
    category text NOT NULL DEFAULT 'general'		-- Free text for grouping tags together
) WITH OIDS;

--------------------------------------------------------------------------------
-- Accounts
--------------------------------------------------------------------------------

-- Accounts
CREATE TABLE persons (
    -- Mandatory
    person_id serial PRIMARY KEY,			-- Account identifier
    email text NOT NULL,				-- E-mail address
    first_name text NOT NULL,				-- First name
    last_name text NOT NULL,				-- Last name
    deleted boolean NOT NULL DEFAULT false,		-- Has been deleted
    enabled boolean NOT NULL DEFAULT false,		-- Has been disabled

    password text NOT NULL DEFAULT 'nopass',		-- Password (md5crypted)
    verification_key text,				-- Reset password key
    verification_expires timestamp without time zone,

    -- Optional
    title text,						-- Honorific
    phone text,						-- Telephone number
    url text,						-- Home page
    bio text,						-- Biography

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
) WITH OIDS;
CREATE INDEX persons_email_idx ON persons (email);

--------------------------------------------------------------------------------
-- person tags
--------------------------------------------------------------------------------
CREATE TABLE person_tag (
    person_tag_id serial PRIMARY KEY,			-- ID
    person_id integer REFERENCES persons NOT NULL,	-- person id
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

--------------------------------------------------------------------------------
-- Sites
--------------------------------------------------------------------------------

-- Sites
CREATE TABLE sites (
    -- Mandatory
    site_id serial PRIMARY KEY,				-- Site identifier
    login_base text NOT NULL,				-- Site slice prefix
    name text NOT NULL,					-- Site name
    abbreviated_name text NOT NULL,			-- Site abbreviated name
    enabled boolean NOT NULL Default true,		-- Is this site enabled
    deleted boolean NOT NULL DEFAULT false,		-- Has been deleted
    is_public boolean NOT NULL DEFAULT true,		-- Shows up in public lists
    max_slices integer NOT NULL DEFAULT 0,		-- Maximum number of slices
    max_slivers integer NOT NULL DEFAULT 1000,		-- Maximum number of instantiated slivers

    -- Optional
    latitude real,
    longitude real,
    url text,
    ext_consortium_id integer,				-- external consortium id

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
) WITH OIDS;
CREATE INDEX sites_login_base_idx ON sites (login_base);

-- Account site membership
CREATE TABLE person_site (
    person_id integer REFERENCES persons NOT NULL,	-- Account identifier
    site_id integer REFERENCES sites NOT NULL,		-- Site identifier
    is_primary boolean NOT NULL DEFAULT false,		-- Is the primary site for this account
    PRIMARY KEY (person_id, site_id)
);
CREATE INDEX person_site_person_id_idx ON person_site (person_id);
CREATE INDEX person_site_site_id_idx ON person_site (site_id);

-- Ordered by primary site first
CREATE OR REPLACE VIEW person_site_ordered AS
SELECT person_id, site_id
FROM person_site
ORDER BY is_primary DESC;

-- Sites that each person is a member of
CREATE OR REPLACE VIEW person_sites AS
SELECT person_id,
array_accum(site_id) AS site_ids
FROM person_site_ordered
GROUP BY person_id;

-- Accounts at each site
CREATE OR REPLACE VIEW site_persons AS
SELECT site_id,
array_accum(person_id) AS person_ids
FROM person_site
GROUP BY site_id;

--------------------------------------------------------------------------------
-- site tags
--------------------------------------------------------------------------------

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

--------------------------------------------------------------------------------
-- Mailing Addresses
--------------------------------------------------------------------------------

CREATE TABLE address_types (
    address_type_id serial PRIMARY KEY,			-- Address type identifier
    name text UNIQUE NOT NULL,				-- Address type
    description text					-- Address type description
) WITH OIDS;

-- Multi-rows insertion "insert .. values (row1), (row2)" is not supported by pgsql-8.1
-- 'Billing' Used to be 'Site'
INSERT INTO address_types (name) VALUES ('Personal');
INSERT INTO address_types (name) VALUES ('Shipping');
INSERT INTO address_types (name) VALUES ('Billing');

-- Mailing addresses
CREATE TABLE addresses (
    address_id serial PRIMARY KEY,			-- Address identifier
    line1 text NOT NULL,				-- Address line 1
    line2 text,						-- Address line 2
    line3 text,						-- Address line 3
    city text NOT NULL,					-- City
    state text NOT NULL,				-- State or province
    postalcode text NOT NULL,				-- Postal code
    country text NOT NULL				-- Country
) WITH OIDS;

-- Each mailing address can be one of several types
CREATE TABLE address_address_type (
    address_id integer REFERENCES addresses NOT NULL,		-- Address identifier
    address_type_id integer REFERENCES address_types NOT NULL,	-- Address type
    PRIMARY KEY (address_id, address_type_id)
) WITH OIDS;
CREATE INDEX address_address_type_address_id_idx ON address_address_type (address_id);
CREATE INDEX address_address_type_address_type_id_idx ON address_address_type (address_type_id);

CREATE OR REPLACE VIEW address_address_types AS
SELECT address_id,
array_accum(address_type_id) AS address_type_ids,
array_accum(address_types.name) AS address_types
FROM address_address_type
LEFT JOIN address_types USING (address_type_id)
GROUP BY address_id;

CREATE TABLE site_address (
    site_id integer REFERENCES sites NOT NULL,		-- Site identifier
    address_id integer REFERENCES addresses NOT NULL,	-- Address identifier
    PRIMARY KEY (site_id, address_id)
) WITH OIDS;
CREATE INDEX site_address_site_id_idx ON site_address (site_id);
CREATE INDEX site_address_address_id_idx ON site_address (address_id);

CREATE OR REPLACE VIEW site_addresses AS
SELECT site_id,
array_accum(address_id) AS address_ids
FROM site_address
GROUP BY site_id;

--------------------------------------------------------------------------------
-- Authentication Keys
--------------------------------------------------------------------------------

-- Valid key types
CREATE TABLE key_types (
    key_type text PRIMARY KEY				-- Key type
) WITH OIDS;
INSERT INTO key_types (key_type) VALUES ('ssh');

-- Authentication keys
CREATE TABLE keys (
    key_id serial PRIMARY KEY,				-- Key identifier
    key_type text REFERENCES key_types NOT NULL,	-- Key type
    key text NOT NULL, -- Key material
    is_blacklisted boolean NOT NULL DEFAULT false	-- Has been blacklisted
) WITH OIDS;

-- Account authentication key(s)
CREATE TABLE person_key (
    key_id integer REFERENCES keys PRIMARY KEY,		-- Key identifier
    person_id integer REFERENCES persons NOT NULL	-- Account identifier
) WITH OIDS;
CREATE INDEX person_key_person_id_idx ON person_key (person_id);

CREATE OR REPLACE VIEW person_keys AS
SELECT person_id,
array_accum(key_id) AS key_ids
FROM person_key
GROUP BY person_id;

--------------------------------------------------------------------------------
-- Account roles
--------------------------------------------------------------------------------

CREATE TABLE person_role (
    person_id integer REFERENCES persons NOT NULL,	-- Account identifier
    role_id integer REFERENCES roles NOT NULL,		-- Role identifier
    PRIMARY KEY (person_id, role_id)
) WITH OIDS;
CREATE INDEX person_role_person_id_idx ON person_role (person_id);

-- Account roles
CREATE OR REPLACE VIEW person_roles AS
SELECT person_id,
array_accum(role_id) AS role_ids,
array_accum(roles.name) AS roles
FROM person_role
LEFT JOIN roles USING (role_id)
GROUP BY person_id;

--------------------------------------------------------------------------------
-- Nodes
--------------------------------------------------------------------------------

-- Valid node boot states (Nodes.py expect max length to be 20)
CREATE TABLE boot_states (
    boot_state text PRIMARY KEY
) WITH OIDS;
INSERT INTO boot_states (boot_state) VALUES ('boot');
INSERT INTO boot_states (boot_state) VALUES ('safeboot');
INSERT INTO boot_states (boot_state) VALUES ('reinstall');
INSERT INTO boot_states (boot_state) VALUES ('disabled');

CREATE TABLE run_levels  (
    run_level text PRIMARY KEY
) WITH OIDS;
INSERT INTO run_levels  (run_level) VALUES ('boot');
INSERT INTO run_levels  (run_level) VALUES ('safeboot');
INSERT INTO run_levels  (run_level) VALUES ('failboot');
INSERT INTO run_levels  (run_level) VALUES ('reinstall');

-- Known node types (Nodes.py expect max length to be 20)
CREATE TABLE node_types (
    node_type text PRIMARY KEY
) WITH OIDS;
INSERT INTO node_types (node_type) VALUES ('regular');
-- old dummynet stuff, to be removed
INSERT INTO node_types (node_type) VALUES ('dummynet');

-- Nodes
CREATE TABLE nodes (
    -- Mandatory
    node_id serial PRIMARY KEY,				-- Node identifier
    node_type text REFERENCES node_types		-- node type
    	       DEFAULT 'regular',

    hostname text NOT NULL,				-- Node hostname
    site_id integer REFERENCES sites NOT NULL,		-- At which site 
    boot_state text REFERENCES boot_states NOT NULL	-- Node boot state
    	       DEFAULT 'reinstall', 
    run_level  text REFERENCES run_levels DEFAULT NULL, -- Node Run Level
    deleted boolean NOT NULL DEFAULT false,		-- Is deleted

    -- Optional
    model text,						-- Hardware make and model
    boot_nonce text,					-- Random nonce updated by Boot Manager
    version text,					-- Boot CD version string updated by Boot Manager
    ssh_rsa_key text,					-- SSH host key updated by Boot Manager
    key text,						-- Node key generated when boot file is downloaded
	verified boolean NOT NULL DEFAULT false,	-- whether or not the node & pcu are verified

    -- Timestamps
    date_created timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_download timestamp without time zone,
    last_pcu_reboot timestamp without time zone,
    last_pcu_confirmation timestamp without time zone,
    last_contact timestamp without time zone 	
) WITH OIDS;
CREATE INDEX nodes_hostname_idx ON nodes (hostname);
CREATE INDEX nodes_site_id_idx ON nodes (site_id);

-- Nodes at each site
CREATE OR REPLACE VIEW site_nodes AS
SELECT site_id,
array_accum(node_id) AS node_ids
FROM nodes
WHERE deleted IS false
GROUP BY site_id;

--------------------------------------------------------------------------------
-- node tags
--------------------------------------------------------------------------------

CREATE TABLE node_tag (
    node_tag_id serial PRIMARY KEY,			-- ID
    node_id integer REFERENCES nodes NOT NULL,		-- node id
    tag_type_id integer REFERENCES tag_types,		-- tag type id
    value text						-- value attached
) WITH OIDS;

--------------------------------------------------------------------------------
-- (network) interfaces
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

-- Network interfaces
CREATE TABLE interfaces (
    -- Mandatory
    interface_id serial PRIMARY KEY,			-- Network interface identifier
    node_id integer REFERENCES nodes NOT NULL,		-- Which node
    is_primary boolean NOT NULL DEFAULT false,		-- Is the primary interface for this node
    type text REFERENCES network_types NOT NULL,	-- Addressing scheme
    method text REFERENCES network_methods NOT NULL,	-- Configuration method

    -- Optional, depending on type and method
    ip text,						-- IP address
    mac text,						-- MAC address
    gateway text,					-- Default gateway address
    network text,					-- Network address
    broadcast text,					-- Network broadcast address
    netmask text,					-- Network mask
    dns1 text,						-- Primary DNS server
    dns2 text,						-- Secondary DNS server
    bwlimit integer,					-- Bandwidth limit in bps
    hostname text,					-- Hostname of this interface
    last_updated timestamp without time zone -- When the interface was last updated
) WITH OIDS;
CREATE INDEX interfaces_node_id_idx ON interfaces (node_id);

-- Ordered by primary interface first
CREATE OR REPLACE VIEW interfaces_ordered AS
SELECT node_id, interface_id
FROM interfaces
ORDER BY is_primary DESC;

-- Network interfaces on each node
CREATE OR REPLACE VIEW node_interfaces AS
SELECT node_id,
array_accum(interface_id) AS interface_ids
FROM interfaces_ordered
GROUP BY node_id;

--------------------------------------------------------------------------------
-- Interface tags (formerly known as interface settings)
--------------------------------------------------------------------------------

CREATE TABLE interface_tag (
    interface_tag_id serial PRIMARY KEY,		-- Interface Setting Identifier
    interface_id integer REFERENCES interfaces NOT NULL,-- the interface this applies to
    tag_type_id integer REFERENCES tag_types NOT NULL,	-- the setting type
    value text						-- value attached
) WITH OIDS;

CREATE OR REPLACE VIEW interface_tags AS 
SELECT interface_id,
array_accum(interface_tag_id) AS interface_tag_ids
FROM interface_tag
GROUP BY interface_id;

CREATE OR REPLACE VIEW view_interface_tags AS
SELECT
interface_tag.interface_tag_id,
interface_tag.interface_id,
interfaces.ip,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
tag_types.min_role_id,
interface_tag.value
FROM interface_tag
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN interfaces USING (interface_id);

CREATE OR REPLACE VIEW view_interfaces AS
SELECT
interfaces.interface_id,
interfaces.node_id,
interfaces.is_primary,
interfaces.type,
interfaces.method,
interfaces.ip,
interfaces.mac,
interfaces.gateway,
interfaces.network,
interfaces.broadcast,
interfaces.netmask,
interfaces.dns1,
interfaces.dns2,
interfaces.bwlimit,
interfaces.hostname,
CAST(date_part('epoch', interfaces.last_updated) AS bigint) AS last_updated,
COALESCE((SELECT interface_tag_ids FROM interface_tags WHERE interface_tags.interface_id = interfaces.interface_id), '{}') AS interface_tag_ids
FROM interfaces;

--------------------------------------------------------------------------------
-- ilinks : links between interfaces
--------------------------------------------------------------------------------
CREATE TABLE ilink (
       ilink_id serial PRIMARY KEY,				-- id
       tag_type_id integer REFERENCES tag_types,		-- id of the tag type
       src_interface_id integer REFERENCES interfaces not NULL,	-- id of src interface
       dst_interface_id integer REFERENCES interfaces NOT NULL, -- id of dst interface
       value text						-- optional value on the link
) WITH OIDS;

CREATE OR REPLACE VIEW view_ilinks AS
SELECT * FROM tag_types 
INNER JOIN ilink USING (tag_type_id);

-- xxx TODO : expose to view_interfaces the set of ilinks a given interface is part of
-- this is needed for properly deleting these ilinks when an interface gets deleted
-- as this is not done yet, it prevents DeleteInterface, thus DeleteNode, thus DeleteSite
-- from working correctly when an iLink is set

--------------------------------------------------------------------------------
-- Node groups
--------------------------------------------------------------------------------

-- Node groups
CREATE TABLE nodegroups (
    nodegroup_id serial PRIMARY KEY,		-- Group identifier
    groupname text UNIQUE NOT NULL,		-- Group name 
    tag_type_id integer REFERENCES tag_types,	-- node is in nodegroup if it has this tag defined
    -- can be null, make management faster & easier
    value text					-- with this value attached
) WITH OIDS;

-- xxx - first rough implem. similar to former semantics but might be slow
CREATE OR REPLACE VIEW nodegroup_node AS
SELECT nodegroup_id, node_id 
FROM tag_types 
JOIN node_tag 
USING (tag_type_id) 
JOIN nodegroups 
USING (tag_type_id,value);

CREATE OR REPLACE VIEW nodegroup_nodes AS
SELECT nodegroup_id,
array_accum(node_id) AS node_ids
FROM nodegroup_node
GROUP BY nodegroup_id;

-- Node groups that each node is a member of
CREATE OR REPLACE VIEW node_nodegroups AS
SELECT node_id,
array_accum(nodegroup_id) AS nodegroup_ids
FROM nodegroup_node
GROUP BY node_id;

--------------------------------------------------------------------------------
-- Node configuration files
--------------------------------------------------------------------------------

CREATE TABLE conf_files (
    conf_file_id serial PRIMARY KEY,			-- Configuration file identifier
    enabled bool NOT NULL DEFAULT true,			-- Configuration file is active
    source text NOT NULL,				-- Relative path on the boot server
							-- where file can be downloaded
    dest text NOT NULL,					-- Absolute path where file should be installed
    file_permissions text NOT NULL DEFAULT '0644',	-- chmod(1) permissions
    file_owner text NOT NULL DEFAULT 'root',		-- chown(1) owner
    file_group text NOT NULL DEFAULT 'root',		-- chgrp(1) owner
    preinstall_cmd text,				-- Shell command to execute prior to installing
    postinstall_cmd text,				-- Shell command to execute after installing
    error_cmd text,					-- Shell command to execute if any error occurs
    ignore_cmd_errors bool NOT NULL DEFAULT false,	-- Install file anyway even if an error occurs
    always_update bool NOT NULL DEFAULT false		-- Always attempt to install file even if unchanged
) WITH OIDS;

CREATE TABLE conf_file_node (
    conf_file_id integer REFERENCES conf_files NOT NULL,	-- Configuration file identifier
    node_id integer REFERENCES nodes NOT NULL,			-- Node identifier
    PRIMARY KEY (conf_file_id, node_id)
);
CREATE INDEX conf_file_node_conf_file_id_idx ON conf_file_node (conf_file_id);
CREATE INDEX conf_file_node_node_id_idx ON conf_file_node (node_id);

-- Nodes linked to each configuration file
CREATE OR REPLACE VIEW conf_file_nodes AS
SELECT conf_file_id,
array_accum(node_id) AS node_ids
FROM conf_file_node
GROUP BY conf_file_id;

-- Configuration files linked to each node
CREATE OR REPLACE VIEW node_conf_files AS
SELECT node_id,
array_accum(conf_file_id) AS conf_file_ids
FROM conf_file_node
GROUP BY node_id;

CREATE TABLE conf_file_nodegroup (
    conf_file_id integer REFERENCES conf_files NOT NULL,	-- Configuration file identifier
    nodegroup_id integer REFERENCES nodegroups NOT NULL,	-- Node group identifier
    PRIMARY KEY (conf_file_id, nodegroup_id)
);
CREATE INDEX conf_file_nodegroup_conf_file_id_idx ON conf_file_nodegroup (conf_file_id);
CREATE INDEX conf_file_nodegroup_nodegroup_id_idx ON conf_file_nodegroup (nodegroup_id);

-- Node groups linked to each configuration file
CREATE OR REPLACE VIEW conf_file_nodegroups AS
SELECT conf_file_id,
array_accum(nodegroup_id) AS nodegroup_ids
FROM conf_file_nodegroup
GROUP BY conf_file_id;

-- Configuration files linked to each node group
CREATE OR REPLACE VIEW nodegroup_conf_files AS
SELECT nodegroup_id,
array_accum(conf_file_id) AS conf_file_ids
FROM conf_file_nodegroup
GROUP BY nodegroup_id;

--------------------------------------------------------------------------------
-- Power control units (PCUs)
--------------------------------------------------------------------------------

CREATE TABLE pcus (
    -- Mandatory
    pcu_id serial PRIMARY KEY,				-- PCU identifier
    site_id integer REFERENCES sites NOT NULL,		-- Site identifier
    hostname text,					-- Hostname, not necessarily unique 
							-- (multiple logical sites could use the same PCU)
    ip text NOT NULL,					-- IP, not necessarily unique

    -- Optional
    protocol text,					-- Protocol, e.g. ssh or https or telnet
    username text,					-- Username, if applicable
    "password" text,					-- Password, if applicable
    model text,						-- Model, e.g. BayTech or iPal
    last_updated timestamp without time zone,
    notes text						-- Random notes
) WITH OIDS;
CREATE INDEX pcus_site_id_idx ON pcus (site_id);

CREATE OR REPLACE VIEW site_pcus AS
SELECT site_id,
array_accum(pcu_id) AS pcu_ids
FROM pcus
GROUP BY site_id;

CREATE TABLE pcu_node (
    pcu_id integer REFERENCES pcus NOT NULL,		-- PCU identifier
    node_id integer REFERENCES nodes NOT NULL,		-- Node identifier
    port integer NOT NULL,				-- Port number
    PRIMARY KEY (pcu_id, node_id),			-- The same node cannot be controlled by different ports
    UNIQUE (pcu_id, port)				-- The same port cannot control multiple nodes
);
CREATE INDEX pcu_node_pcu_id_idx ON pcu_node (pcu_id);
CREATE INDEX pcu_node_node_id_idx ON pcu_node (node_id);

CREATE OR REPLACE VIEW node_pcus AS
SELECT node_id,
array_accum(pcu_id) AS pcu_ids,
array_accum(port) AS ports
FROM pcu_node
GROUP BY node_id;

CREATE OR REPLACE VIEW pcu_nodes AS
SELECT pcu_id,
array_accum(node_id) AS node_ids,
array_accum(port) AS ports
FROM pcu_node
GROUP BY pcu_id;

--------------------------------------------------------------------------------
-- Slices
--------------------------------------------------------------------------------

CREATE TABLE slice_instantiations (
    instantiation text PRIMARY KEY
) WITH OIDS;
INSERT INTO slice_instantiations (instantiation) VALUES ('not-instantiated');	-- Placeholder slice
INSERT INTO slice_instantiations (instantiation) VALUES ('plc-instantiated');	-- Instantiated by Node Manager
INSERT INTO slice_instantiations (instantiation) VALUES ('delegated');		-- Manually instantiated
INSERT INTO slice_instantiations (instantiation) VALUES ('nm-controller');	-- NM Controller

-- Slices
CREATE TABLE slices (
    slice_id serial PRIMARY KEY,			-- Slice identifier
    site_id integer REFERENCES sites NOT NULL,		-- Site identifier

    name text NOT NULL,					-- Slice name
    instantiation text REFERENCES slice_instantiations  -- Slice state, e.g. plc-instantiated
    		  NOT NULL DEFAULT 'plc-instantiated', 			
    url text,						-- Project URL
    description text,					-- Project description

    max_nodes integer NOT NULL DEFAULT 100,		-- Maximum number of nodes that can be assigned to this slice

    creator_person_id integer REFERENCES persons,	-- Creator
    created timestamp without time zone NOT NULL	-- Creation date
        DEFAULT CURRENT_TIMESTAMP, 
    expires timestamp without time zone NOT NULL	-- Expiration date
        DEFAULT CURRENT_TIMESTAMP + '2 weeks', 

    is_deleted boolean NOT NULL DEFAULT false
) WITH OIDS;
CREATE INDEX slices_site_id_idx ON slices (site_id);
CREATE INDEX slices_name_idx ON slices (name);

-- Slivers
CREATE TABLE slice_node (
    slice_id integer REFERENCES slices NOT NULL,	-- Slice identifier
    node_id integer REFERENCES nodes NOT NULL,		-- Node identifier
    PRIMARY KEY (slice_id, node_id)
) WITH OIDS;
CREATE INDEX slice_node_slice_id_idx ON slice_node (slice_id);
CREATE INDEX slice_node_node_id_idx ON slice_node (node_id);

-- Synonym for slice_node
CREATE OR REPLACE VIEW slivers AS
SELECT * FROM slice_node;

-- Nodes in each slice
CREATE OR REPLACE VIEW slice_nodes AS
SELECT slice_id,
array_accum(node_id) AS node_ids
FROM slice_node
GROUP BY slice_id;

-- Slices on each node
CREATE OR REPLACE VIEW node_slices AS
SELECT node_id,
array_accum(slice_id) AS slice_ids
FROM slice_node
GROUP BY node_id;

-- Slices at each site
CREATE OR REPLACE VIEW site_slices AS
SELECT site_id,
array_accum(slice_id) AS slice_ids
FROM slices
WHERE is_deleted is false
GROUP BY site_id;

-- Slice membership
CREATE TABLE slice_person (
    slice_id integer REFERENCES slices NOT NULL,	-- Slice identifier
    person_id integer REFERENCES persons NOT NULL,	-- Account identifier
    PRIMARY KEY (slice_id, person_id)
) WITH OIDS;
CREATE INDEX slice_person_slice_id_idx ON slice_person (slice_id);
CREATE INDEX slice_person_person_id_idx ON slice_person (person_id);

-- Members of the slice
CREATE OR REPLACE VIEW slice_persons AS
SELECT slice_id,
array_accum(person_id) AS person_ids
FROM slice_person
GROUP BY slice_id;

-- Slices of which each person is a member
CREATE OR REPLACE VIEW person_slices AS
SELECT person_id,
array_accum(slice_id) AS slice_ids
FROM slice_person
GROUP BY person_id;

--------------------------------------------------------------------------------
-- Slice whitelist
--------------------------------------------------------------------------------
-- slice whitelist on nodes
CREATE TABLE node_slice_whitelist (
    node_id integer REFERENCES nodes NOT NULL,		-- Node id of whitelist
    slice_id integer REFERENCES slices NOT NULL,	-- Slice id thats allowd on this node
    PRIMARY KEY (node_id, slice_id)
) WITH OIDS;
CREATE INDEX node_slice_whitelist_node_id_idx ON node_slice_whitelist (node_id);
CREATE INDEX node_slice_whitelist_slice_id_idx ON node_slice_whitelist (slice_id);

-- Slices on each node
CREATE OR REPLACE VIEW node_slices_whitelist AS
SELECT node_id,
array_accum(slice_id) AS slice_ids_whitelist
FROM node_slice_whitelist
GROUP BY node_id;

--------------------------------------------------------------------------------
-- Slice tags (formerly known as slice attributes)
--------------------------------------------------------------------------------

-- Slice/sliver attributes
CREATE TABLE slice_tag (
    slice_tag_id serial PRIMARY KEY,			-- Slice attribute identifier
    slice_id integer REFERENCES slices NOT NULL,	-- Slice identifier
    node_id integer REFERENCES nodes,			-- Sliver attribute if set
    nodegroup_id integer REFERENCES nodegroups,		-- Node group attribute if set
    tag_type_id integer REFERENCES tag_types NOT NULL,	-- Attribute type identifier
    value text
) WITH OIDS;
CREATE INDEX slice_tag_slice_id_idx ON slice_tag (slice_id);
CREATE INDEX slice_tag_node_id_idx ON slice_tag (node_id);
CREATE INDEX slice_tag_nodegroup_id_idx ON slice_tag (nodegroup_id);

--------------------------------------------------------------------------------
-- Initscripts
--------------------------------------------------------------------------------

-- Initscripts
CREATE TABLE initscripts (
    initscript_id serial PRIMARY KEY,			-- Initscript identifier
    name text NOT NULL,					-- Initscript name
    enabled bool NOT NULL DEFAULT true,			-- Initscript is active
    script text NOT NULL,				-- Initscript code
    UNIQUE (name)
) WITH OIDS;
CREATE INDEX initscripts_name_idx ON initscripts (name);


--------------------------------------------------------------------------------
-- Peers
--------------------------------------------------------------------------------

-- Peers
CREATE TABLE peers (
    peer_id serial PRIMARY KEY,				-- Peer identifier
    peername text NOT NULL,				-- Peer name
    peer_url text NOT NULL,				-- (HTTPS) URL of the peer PLCAPI interface
    cacert text,					-- (SSL) Public certificate of peer API server
    key text,						-- (GPG) Public key used for authentication
    shortname text,					-- abbreviated name for displaying foreign objects
    hrn_root text,					-- root for this peer domain
    deleted boolean NOT NULL DEFAULT false
) WITH OIDS;
CREATE INDEX peers_peername_idx ON peers (peername) WHERE deleted IS false;
CREATE INDEX peers_shortname_idx ON peers (shortname) WHERE deleted IS false;

-- Objects at each peer
CREATE TABLE peer_site (
    site_id integer REFERENCES sites PRIMARY KEY,	-- Local site identifier
    peer_id integer REFERENCES peers NOT NULL,		-- Peer identifier
    peer_site_id integer NOT NULL,			-- Foreign site identifier at peer
    UNIQUE (peer_id, peer_site_id)			-- The same foreign site should not be cached twice
) WITH OIDS;
CREATE INDEX peer_site_peer_id_idx ON peers (peer_id);

CREATE OR REPLACE VIEW peer_sites AS
SELECT peer_id,
array_accum(site_id) AS site_ids,
array_accum(peer_site_id) AS peer_site_ids
FROM peer_site
GROUP BY peer_id;

CREATE TABLE peer_person (
    person_id integer REFERENCES persons PRIMARY KEY,	-- Local user identifier
    peer_id integer REFERENCES peers NOT NULL,		-- Peer identifier
    peer_person_id integer NOT NULL,			-- Foreign user identifier at peer
    UNIQUE (peer_id, peer_person_id)			-- The same foreign user should not be cached twice
) WITH OIDS;
CREATE INDEX peer_person_peer_id_idx ON peer_person (peer_id);

CREATE OR REPLACE VIEW peer_persons AS
SELECT peer_id,
array_accum(person_id) AS person_ids,
array_accum(peer_person_id) AS peer_person_ids
FROM peer_person
GROUP BY peer_id;

CREATE TABLE peer_key (
    key_id integer REFERENCES keys PRIMARY KEY,		-- Local key identifier
    peer_id integer REFERENCES peers NOT NULL,		-- Peer identifier
    peer_key_id integer NOT NULL,			-- Foreign key identifier at peer
    UNIQUE (peer_id, peer_key_id)			-- The same foreign key should not be cached twice
) WITH OIDS;
CREATE INDEX peer_key_peer_id_idx ON peer_key (peer_id);

CREATE OR REPLACE VIEW peer_keys AS
SELECT peer_id,
array_accum(key_id) AS key_ids,
array_accum(peer_key_id) AS peer_key_ids
FROM peer_key
GROUP BY peer_id;

CREATE TABLE peer_node (
    node_id integer REFERENCES nodes PRIMARY KEY,	-- Local node identifier
    peer_id integer REFERENCES peers NOT NULL,		-- Peer identifier
    peer_node_id integer NOT NULL,			-- Foreign node identifier
    UNIQUE (peer_id, peer_node_id)			-- The same foreign node should not be cached twice
) WITH OIDS;
CREATE INDEX peer_node_peer_id_idx ON peer_node (peer_id);

CREATE OR REPLACE VIEW peer_nodes AS
SELECT peer_id,
array_accum(node_id) AS node_ids,
array_accum(peer_node_id) AS peer_node_ids
FROM peer_node
GROUP BY peer_id;

CREATE TABLE peer_slice (
    slice_id integer REFERENCES slices PRIMARY KEY,	-- Local slice identifier
    peer_id integer REFERENCES peers NOT NULL,		-- Peer identifier
    peer_slice_id integer NOT NULL,			-- Slice identifier at peer
    UNIQUE (peer_id, peer_slice_id)			-- The same foreign slice should not be cached twice
) WITH OIDS;
CREATE INDEX peer_slice_peer_id_idx ON peer_slice (peer_id);

CREATE OR REPLACE VIEW peer_slices AS
SELECT peer_id,
array_accum(slice_id) AS slice_ids,
array_accum(peer_slice_id) AS peer_slice_ids
FROM peer_slice
GROUP BY peer_id;

--------------------------------------------------------------------------------
-- Authenticated sessions
--------------------------------------------------------------------------------

-- Authenticated sessions
CREATE TABLE sessions (
    session_id text PRIMARY KEY,			-- Session identifier
    expires timestamp without time zone
) WITH OIDS;

-- People can have multiple sessions
CREATE TABLE person_session (
    person_id integer REFERENCES persons NOT NULL,	-- Account identifier
    session_id text REFERENCES sessions NOT NULL,	-- Session identifier
    PRIMARY KEY (person_id, session_id),
    UNIQUE (session_id)					-- Sessions are unique
) WITH OIDS;
CREATE INDEX person_session_person_id_idx ON person_session (person_id);

-- Nodes can have only one session
CREATE TABLE node_session (
    node_id integer REFERENCES nodes NOT NULL,		-- Node identifier
    session_id text REFERENCES sessions NOT NULL,	-- Session identifier
    UNIQUE (node_id),					-- Nodes can have only one session
    UNIQUE (session_id)					-- Sessions are unique
) WITH OIDS;

-------------------------------------------------------------------------------
-- PCU Types
------------------------------------------------------------------------------
CREATE TABLE pcu_types (
    pcu_type_id serial PRIMARY KEY,
    model text NOT NULL ,				-- PCU model name
    name text						-- Full PCU model name
) WITH OIDS;
CREATE INDEX pcu_types_model_idx ON pcu_types (model);

CREATE TABLE pcu_protocol_type (
    pcu_protocol_type_id serial PRIMARY KEY,
    pcu_type_id integer REFERENCES pcu_types NOT NULL,  -- PCU type identifier
    port integer NOT NULL,                              -- PCU port
    protocol text NOT NULL,                             -- Protocol
    supported boolean NOT NULL DEFAULT True             -- Does PLC support
) WITH OIDS;
CREATE INDEX pcu_protocol_type_pcu_type_id ON pcu_protocol_type (pcu_type_id);


CREATE OR REPLACE VIEW pcu_protocol_types AS
SELECT pcu_type_id,
array_accum(pcu_protocol_type_id) as pcu_protocol_type_ids
FROM pcu_protocol_type
GROUP BY pcu_type_id;

--------------------------------------------------------------------------------
-- Message templates
--------------------------------------------------------------------------------

CREATE TABLE messages (
    message_id text PRIMARY KEY,			-- Message name
    subject text,					-- Message summary
    template text,					-- Message template
    enabled bool NOT NULL DEFAULT true			-- Whether message is enabled
) WITH OIDS;

--------------------------------------------------------------------------------
-- Events
--------------------------------------------------------------------------------

-- Events
CREATE TABLE events (
    event_id serial PRIMARY KEY,			-- Event identifier
    person_id integer REFERENCES persons,		-- Person responsible for event, if any
    node_id integer REFERENCES nodes,			-- Node responsible for event, if any
    auth_type text,					-- Type of auth used. i.e. AuthMethod
    fault_code integer NOT NULL DEFAULT 0,		-- Did this event result in error
    call_name text NOT NULL,				-- Call responsible for this event
    call text NOT NULL,					-- Call responsible for this event, including parameters
    message text,					-- High level description of this event
    runtime float DEFAULT 0,				-- Event run time
    time timestamp without time zone NOT NULL		-- Event timestamp
        DEFAULT CURRENT_TIMESTAMP
) WITH OIDS;

-- Database object(s) that may have been affected by a particular event
CREATE TABLE event_object (
    event_id integer REFERENCES events NOT NULL,	-- Event identifier
    object_id integer NOT NULL,				-- Object identifier
    object_type text NOT NULL Default 'Unknown'		-- What type of object is this event affecting
) WITH OIDS;
CREATE INDEX event_object_event_id_idx ON event_object (event_id);
CREATE INDEX event_object_object_id_idx ON event_object (object_id);
CREATE INDEX event_object_object_type_idx ON event_object (object_type);

CREATE OR REPLACE VIEW event_objects AS
SELECT event_id,
array_accum(object_id) AS object_ids,
array_accum(object_type) AS object_types
FROM event_object
GROUP BY event_id;

--------------------------------------------------------------------------------
-- Useful views
--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_pcu_types AS
SELECT
pcu_types.pcu_type_id,
pcu_types.model,
pcu_types.name,
COALESCE((SELECT pcu_protocol_type_ids FROM pcu_protocol_types
		 WHERE pcu_protocol_types.pcu_type_id = pcu_types.pcu_type_id), '{}') 
AS pcu_protocol_type_ids
FROM pcu_types;

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_events AS
SELECT
events.event_id,
events.person_id,
events.node_id,
events.auth_type,
events.fault_code,
events.call_name,
events.call,
events.message,
events.runtime,
CAST(date_part('epoch', events.time) AS bigint) AS time,
COALESCE((SELECT object_ids FROM event_objects WHERE event_objects.event_id = events.event_id), '{}') AS object_ids,
COALESCE((SELECT object_types FROM event_objects WHERE event_objects.event_id = events.event_id), '{}') AS object_types
FROM events;

CREATE OR REPLACE VIEW view_event_objects AS 
SELECT
events.event_id,
events.person_id,
events.node_id,
events.fault_code,
events.call_name,
events.call,
events.message,
events.runtime,
CAST(date_part('epoch', events.time) AS bigint) AS time,
event_object.object_id,
event_object.object_type
FROM events LEFT JOIN event_object USING (event_id);

--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_peers AS
SELECT 
peers.*, 
COALESCE((SELECT site_ids FROM peer_sites WHERE peer_sites.peer_id = peers.peer_id), '{}') AS site_ids,
COALESCE((SELECT peer_site_ids FROM peer_sites WHERE peer_sites.peer_id = peers.peer_id), '{}') AS peer_site_ids,
COALESCE((SELECT person_ids FROM peer_persons WHERE peer_persons.peer_id = peers.peer_id), '{}') AS person_ids,
COALESCE((SELECT peer_person_ids FROM peer_persons WHERE peer_persons.peer_id = peers.peer_id), '{}') AS peer_person_ids,
COALESCE((SELECT key_ids FROM peer_keys WHERE peer_keys.peer_id = peers.peer_id), '{}') AS key_ids,
COALESCE((SELECT peer_key_ids FROM peer_keys WHERE peer_keys.peer_id = peers.peer_id), '{}') AS peer_key_ids,
COALESCE((SELECT node_ids FROM peer_nodes WHERE peer_nodes.peer_id = peers.peer_id), '{}') AS node_ids,
COALESCE((SELECT peer_node_ids FROM peer_nodes WHERE peer_nodes.peer_id = peers.peer_id), '{}') AS peer_node_ids,
COALESCE((SELECT slice_ids FROM peer_slices WHERE peer_slices.peer_id = peers.peer_id), '{}') AS slice_ids,
COALESCE((SELECT peer_slice_ids FROM peer_slices WHERE peer_slices.peer_id = peers.peer_id), '{}') AS peer_slice_ids
FROM peers;

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW node_tags AS
SELECT node_id,
array_accum(node_tag_id) AS node_tag_ids
FROM node_tag
GROUP BY node_id;

CREATE OR REPLACE VIEW view_node_tags AS
SELECT
node_tag.node_tag_id,
node_tag.node_id,
nodes.hostname,
tag_types.tag_type_id,
tag_types.tagname,
tag_types.description,
tag_types.category,
tag_types.min_role_id,
node_tag.value
FROM node_tag 
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN nodes USING (node_id);

CREATE OR REPLACE VIEW view_nodes AS
SELECT
nodes.node_id,
nodes.node_type,
nodes.hostname,
nodes.site_id,
nodes.boot_state,
nodes.run_level,
nodes.deleted,
nodes.model,
nodes.boot_nonce,
nodes.version,
nodes.verified,
nodes.ssh_rsa_key,
nodes.key,
CAST(date_part('epoch', nodes.date_created) AS bigint) AS date_created,
CAST(date_part('epoch', nodes.last_updated) AS bigint) AS last_updated,
CAST(date_part('epoch', nodes.last_contact) AS bigint) AS last_contact,  
CAST(date_part('epoch', nodes.last_boot) AS bigint) AS last_boot,  
CAST(date_part('epoch', nodes.last_download) AS bigint) AS last_download,  
CAST(date_part('epoch', nodes.last_pcu_reboot) AS bigint) AS last_pcu_reboot,  
CAST(date_part('epoch', nodes.last_pcu_confirmation) AS bigint) AS last_pcu_confirmation,  
peer_node.peer_id,
peer_node.peer_node_id,
COALESCE((SELECT interface_ids FROM node_interfaces 
		 WHERE node_interfaces.node_id = nodes.node_id), '{}') 
AS interface_ids,
COALESCE((SELECT nodegroup_ids FROM node_nodegroups 
		 WHERE node_nodegroups.node_id = nodes.node_id), '{}') 
AS nodegroup_ids,
COALESCE((SELECT slice_ids FROM node_slices 
		 WHERE node_slices.node_id = nodes.node_id), '{}') 
AS slice_ids,
COALESCE((SELECT slice_ids_whitelist FROM node_slices_whitelist 
		 WHERE node_slices_whitelist.node_id = nodes.node_id), '{}') 
AS slice_ids_whitelist,
COALESCE((SELECT pcu_ids FROM node_pcus 
		 WHERE node_pcus.node_id = nodes.node_id), '{}') 
AS pcu_ids,
COALESCE((SELECT ports FROM node_pcus
		 WHERE node_pcus.node_id = nodes.node_id), '{}') 
AS ports,
COALESCE((SELECT conf_file_ids FROM node_conf_files
		 WHERE node_conf_files.node_id = nodes.node_id), '{}') 
AS conf_file_ids,
COALESCE((SELECT node_tag_ids FROM node_tags 
		 WHERE node_tags.node_id = nodes.node_id), '{}') 
AS node_tag_ids,
node_session.session_id AS session
FROM nodes
LEFT JOIN peer_node USING (node_id)
LEFT JOIN node_session USING (node_id);

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_nodegroups AS
SELECT
nodegroups.*,
tag_types.tagname,
COALESCE((SELECT conf_file_ids FROM nodegroup_conf_files 
		 WHERE nodegroup_conf_files.nodegroup_id = nodegroups.nodegroup_id), '{}') 
AS conf_file_ids,
COALESCE((SELECT node_ids FROM nodegroup_nodes 
		 WHERE nodegroup_nodes.nodegroup_id = nodegroups.nodegroup_id), '{}') 
AS node_ids
FROM nodegroups INNER JOIN tag_types USING (tag_type_id);

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_conf_files AS
SELECT
conf_files.*,
COALESCE((SELECT node_ids FROM conf_file_nodes 
		 WHERE conf_file_nodes.conf_file_id = conf_files.conf_file_id), '{}') 
AS node_ids,
COALESCE((SELECT nodegroup_ids FROM conf_file_nodegroups 
		 WHERE conf_file_nodegroups.conf_file_id = conf_files.conf_file_id), '{}') 
AS nodegroup_ids
FROM conf_files;

--------------------------------------------------------------------------------
DROP VIEW view_pcus;
CREATE OR REPLACE VIEW view_pcus AS
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
CAST(date_part('epoch', pcus.last_updated) AS bigint) AS last_updated,
COALESCE((SELECT node_ids FROM pcu_nodes WHERE pcu_nodes.pcu_id = pcus.pcu_id), '{}') AS node_ids,
COALESCE((SELECT ports FROM pcu_nodes WHERE pcu_nodes.pcu_id = pcus.pcu_id), '{}') AS ports
FROM pcus;


--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_addresses AS
SELECT
addresses.*,
COALESCE((SELECT address_type_ids FROM address_address_types WHERE address_address_types.address_id = addresses.address_id), '{}') AS address_type_ids,
COALESCE((SELECT address_types FROM address_address_types WHERE address_address_types.address_id = addresses.address_id), '{}') AS address_types
FROM addresses;

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_keys AS
SELECT
keys.*,
person_key.person_id,
peer_key.peer_id,
peer_key.peer_key_id
FROM keys
LEFT JOIN person_key USING (key_id)
LEFT JOIN peer_key USING (key_id);

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW slice_tags AS
SELECT slice_id,
array_accum(slice_tag_id) AS slice_tag_ids
FROM slice_tag
GROUP BY slice_id;

CREATE OR REPLACE VIEW view_slices AS
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
peer_slice.peer_id,
peer_slice.peer_slice_id,
COALESCE((SELECT node_ids FROM slice_nodes WHERE slice_nodes.slice_id = slices.slice_id), '{}') AS node_ids,
COALESCE((SELECT person_ids FROM slice_persons WHERE slice_persons.slice_id = slices.slice_id), '{}') AS person_ids,
COALESCE((SELECT slice_tag_ids FROM slice_tags WHERE slice_tags.slice_id = slices.slice_id), '{}') AS slice_tag_ids
FROM slices
LEFT JOIN peer_slice USING (slice_id);

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
tag_types.min_role_id,
slice_tag.value,
slices.name
FROM slice_tag
INNER JOIN tag_types USING (tag_type_id)
INNER JOIN slices USING (slice_id);

--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW view_sessions AS
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

INSERT INTO persons (first_name, last_name, email, password, enabled)
VALUES              ('Maintenance', 'Account', 'maint@localhost.localdomain', 'nopass', true);

INSERT INTO person_role (person_id, role_id) VALUES (1, 10);
INSERT INTO person_role (person_id, role_id) VALUES (1, 20);
INSERT INTO person_role (person_id, role_id) VALUES (1, 30);
INSERT INTO person_role (person_id, role_id) VALUES (1, 40);

INSERT INTO sites (login_base, name, abbreviated_name, max_slices)
VALUES ('pl', 'PlanetLab Central', 'PLC', 100);

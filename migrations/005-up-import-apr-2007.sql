--
-- to apply changes from import done in april 2007 from the
-- planetlab-4_0-branch tag
--
-- this is a rather complex example, so for next times, make sure that you
-- * first add new columns and new tables
-- * then create or replace views
-- * and only finally drop columns
-- otherwise the columns may refuse to get dropped if they are still used by views
--

---------- creations 

ALTER TABLE sites ADD ext_consortium_id integer;

ALTER TABLE nodes ADD last_contact timestamp without time zone;

-- Initscripts
CREATE TABLE initscripts (
    initscript_id serial PRIMARY KEY, -- Initscript identifier
    name text NOT NULL, -- Initscript name
    enabled bool NOT NULL DEFAULT true, -- Initscript is active
    script text NOT NULL, -- Initscript
    UNIQUE (name)
) WITH OIDS;
CREATE INDEX initscripts_name_idx ON initscripts (name);

-- rather drop the tables altogether, 
-- ALTER TABLE events ADD auth_type text;
-- ALTER TABLE event_object ADD COLUMN object_type text NOT NULL Default 'Unknown';
-- CREATE INDEX event_object_object_type_idx ON event_object (object_type);

-- for some reason these views require to be dropped first
DROP VIEW view_events;
DROP VIEW event_objects;
DROP VIEW view_nodes;
DROP VIEW view_sites;

----dropping tables must be preceded by dropping views using those tables
----otherwise  dependency problems
DROP TABLE event_object;
DROP TABLE events;

CREATE TABLE events (
    event_id serial PRIMARY KEY,  -- Event identifier
    person_id integer REFERENCES persons, -- Person responsible for event, if any
    node_id integer REFERENCES nodes, -- Node responsible for event, if any
    auth_type text, -- Type of auth used. i.e. AuthMethod
    fault_code integer NOT NULL DEFAULT 0, -- Did this event result in error
    call_name text NOT NULL, -- Call responsible for this event
    call text NOT NULL, -- Call responsible for this event, including parameters
    message text, -- High level description of this event
    runtime float DEFAULT 0, -- Event run time
    time timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP -- Event timestamp
) WITH OIDS;

-- Database object(s) that may have been affected by a particular event
CREATE TABLE event_object (
    event_id integer REFERENCES events NOT NULL, -- Event identifier
    object_id integer NOT NULL, -- Object identifier
    object_type text NOT NULL Default 'Unknown' -- What type of object is this event affecting
) WITH OIDS;
CREATE INDEX event_object_event_id_idx ON event_object (event_id);
CREATE INDEX event_object_object_id_idx ON event_object (object_id);
CREATE INDEX event_object_object_type_idx ON event_object (object_type);

---------- view changes

CREATE OR REPLACE VIEW event_objects AS
SELECT event_id,
array_accum(object_id) AS object_ids,
array_accum(object_type) AS object_types
FROM event_object
GROUP BY event_id;

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

CREATE OR REPLACE VIEW view_nodes AS
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
CAST(date_part('epoch', nodes.last_contact) AS bigint) AS last_contact,  
peer_node.peer_id,
peer_node.peer_node_id,
COALESCE((SELECT nodenetwork_ids FROM node_nodenetworks WHERE node_nodenetworks.node_id = nodes.node_id), '{}') AS nodenetwork_ids,
COALESCE((SELECT nodegroup_ids FROM node_nodegroups WHERE node_nodegroups.node_id = nodes.node_id), '{}') AS nodegroup_ids,
COALESCE((SELECT slice_ids FROM node_slices WHERE node_slices.node_id = nodes.node_id), '{}') AS slice_ids,
COALESCE((SELECT pcu_ids FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS pcu_ids,
COALESCE((SELECT ports FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS ports,
COALESCE((SELECT conf_file_ids FROM node_conf_files WHERE node_conf_files.node_id = nodes.node_id), '{}') AS conf_file_ids,
node_session.session_id AS session
FROM nodes
LEFT JOIN peer_node USING (node_id)
LEFT JOIN node_session USING (node_id);

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
COALESCE((SELECT pcu_ids FROM site_pcus WHERE site_pcus.site_id = sites.site_id), '{}') AS pcu_ids
FROM sites
LEFT JOIN peer_site USING (site_id);

---------- deletions
--dont need to drop this colum it doesn't exit anymore 
-----ALTER TABLE events DROP COLUMN object_type;

---------- bump subversion

UPDATE plc_db_version SET subversion = 5;
SELECT subversion from plc_db_version;

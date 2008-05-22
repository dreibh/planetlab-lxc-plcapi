#!/bin/bash

. /etc/planetlab/plc_config

PLC_DB_USER

# return 0 (yes) or 1 (no) whether the database exists
function check_for_database () {
    dbname=$1; shift
    psql --user=$PLC_DB_USER --quiet -c "SELECT subversion from plc_db_version LIMIT 1" $dbname 2> /dev/null
    return $?
}

# when 'service plc start' gets run, the planetlab5 DB gets created 
# so this script will drop the planetlab5 DB and re-create it from scratch 
# with the contents of the planetlab4 DB that is epxected to exist
function main () {
    
    set -e
    cd /usr/share/plc_api

    # check that planetlab4 exists
    if check_for_database planetlab4 ; then
	echo OK : FOUND db planetlab4
    else
	echo ERROR :  planetlab4 NOT FOUND - exiting 
	exit 1
    fi

    # dump planetlab4
    DUMP4=planetlab4-$(date +%Y-%m-%d-%H-%M)
    pg_dump --user=$PLC_DB_USER planetlab4 > $DUMP4.sql

    # check if planetlab5 exists
    if check_for_database planetlab5 ; then
	echo 'WARNING: found an existing DB named planetlab5'
	i=0
	while true; do
	    i=$(($i+1))
	    bkname=$(printf planetlab5-%03d $i)
	    if check_for_database $bkname ; then
		echo "$bkname already exists - skipping"
	    else
		echo "Renaming planetab5 into $bkname"
		psql --user=$PLC_DB_USER -c "ALTER DATABASE planetlab5 RENAME TO $bkname"
		echo "Done"
	    fi
	done
    fi
    if check_for_database planetlab5 ; then
	echo ERROR : FOUND planetlab5 - exiting
	exit 1
    else
	echo OK : db planetlab5 NOT FOUND 
    fi

    # create it
    createdb --user=postgres --encoding=UNICODE --owner=$PLC_DB_USER planetlab5
    # populate it
    psql --user=$PLC_DB_USER planetlab5 < $DUMP4.sql

    # run coarse-grain script
    migration_script | psql --user=$PLC_DB_USER planetlab5 
    
}


function migration_script () {

    cat <<EOF

-- $Id$
--
-- this is the script to migrate from 4.2 to 5.0
--

----------------------------------------
-- rename nodenetwork into interface
----------------------------------------

ALTER TABLE nodenetworks RENAME TO interfaces;
ALTER TABLE interfaces RENAME COLUMN nodenetwork_id TO interface_id;

ALTER INDEX nodenetworks_node_id_idx RENAME TO interfaces_node_id_idx;

ALTER TABLE nodenetwork_setting_types RENAME TO interface_setting_types;
ALTER TABLE interface_setting_types RENAME COLUMN nodenetwork_setting_type_id TO interface_setting_type_id;

ALTER TABLE nodenetwork_setting RENAME TO interface_setting;

-- views
ALTER TABLE nodenetworks_ordered RENAME TO interfaces_ordered;
ALTER TABLE interfaces_ordered RENAME COLUMN nodenetwork_id TO interface_id;

ALTER TABLE node_nodenetworks RENAME TO node_interfaces;
ALTER TABLE node_interfaces RENAME COLUMN nodenetwork_ids TO interface_ids;

ALTER TABLE nodenetwork_settings RENAME TO interface_settings;
ALTER TABLE interface_settings RENAME COLUMN nodenetwork_id TO interface_id;
ALTER TABLE interface_settings RENAME COLUMN nodenetwork_setting_ids TO setting_ids;

ALTER TABLE view_nodenetwork_settings RENAME TO view_interface_settings;
ALTER TABLE view_interface_settings RENAME COLUMN nodenetwork_setting_id TO interface_setting_id;
ALTER TABLE view_interface_settings RENAME COLUMN nodenetwork_id TO interface_id;
ALTER TABLE view_interface_settings RENAME COLUMN nodenetwork_setting_type_id TO interface_setting_type_id;

ALTER TABLE view_nodenetworks RENAME TO view_interfaces;
ALTER TABLE view_interfaces RENAME COLUMN nodenetwork_id TO interface_id;
ALTER TABLE view_interfaces RENAME COLUMN nodenetwork_setting_ids TO setting_ids;

ALTER TABLE view_nodes RENAME COLUMN nodenetwork_ids TO interface_ids;

----------------------------------------
-- node tags
----------------------------------------
CREATE TABLE node_tag_types (

    node_tag_type_id serial PRIMARY KEY,	-- ID
    name text UNIQUE NOT NULL,	    		-- Tag Name
    description text,				-- Optional Description
    category text NOT NULL,			-- Free text for grouping tags together
    min_role_id integer REFERENCES roles	-- set minimal role required
) WITH OIDS;

CREATE TABLE node_tag (
    node_tag_id serial PRIMARY KEY,		-- ID
    node_id integer REFERENCES nodes NOT NULL,	-- node id
    node_tag_type_id integer REFERENCES node_tag_types,
    		     	       	     	 	-- tag type id
    value text					-- value attached
) WITH OIDS;

---------- related views
CREATE OR REPLACE VIEW node_tags AS
SELECT node_id,
array_accum(node_tag_id) AS tag_ids
FROM node_tag
GROUP BY node_id;

CREATE OR REPLACE VIEW view_node_tags AS
SELECT
node_tag.node_tag_id,
node_tag.node_id,
node_tag_types.node_tag_type_id,
node_tag_types.name,
node_tag_types.description,
node_tag_types.category,
node_tag_types.min_role_id,
node_tag.value
FROM node_tag 
INNER JOIN node_tag_types USING (node_tag_type_id);

DROP VIEW view_nodes;
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
COALESCE((SELECT interface_ids FROM node_interfaces WHERE node_interfaces.node_id = nodes.node_id), '{}') AS interface_ids,
COALESCE((SELECT nodegroup_ids FROM node_nodegroups WHERE node_nodegroups.node_id = nodes.node_id), '{}') AS nodegroup_ids,
COALESCE((SELECT slice_ids FROM node_slices WHERE node_slices.node_id = nodes.node_id), '{}') AS slice_ids,
COALESCE((SELECT slice_ids_whitelist FROM node_slices_whitelist WHERE node_slices_whitelist.node_id = nodes.node_id), '{}') AS slice_ids_whitelist,
COALESCE((SELECT pcu_ids FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS pcu_ids,
COALESCE((SELECT ports FROM node_pcus WHERE node_pcus.node_id = nodes.node_id), '{}') AS ports,
COALESCE((SELECT conf_file_ids FROM node_conf_files WHERE node_conf_files.node_id = nodes.node_id), '{}') AS conf_file_ids,
COALESCE((SELECT tag_ids FROM node_tags WHERE node_tags.node_id = nodes.node_id), '{}') AS tag_ids,
node_session.session_id AS session
FROM nodes
LEFT JOIN peer_node USING (node_id)
LEFT JOIN node_session USING (node_id);

----------------------------------------
-- nodegroups
-- xxx - todo 
-- a more usable migration script would need to capture more data
----------------------------------------
DROP TABLE IF EXISTS nodegroups CASCADE;

-- Node groups
CREATE TABLE nodegroups (
    nodegroup_id serial PRIMARY KEY,			-- Group identifier
    name text UNIQUE NOT NULL,				-- Group name
    node_tag_type_id integer REFERENCES node_tag_types,	-- node is in nodegroup if it has this tag defined
    value text						-- with value 'value'
) WITH OIDS;

CREATE OR REPLACE VIEW nodegroup_node AS
SELECT nodegroup_id, node_id 
FROM node_tag_types 
JOIN node_tag 
USING (node_tag_type_id) 
JOIN nodegroups 
USING (node_tag_type_id,value);

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

----------------------------------------
-- update versioning
----------------------------------------
UPDATE plc_db_version SET version=5, subversion=0;

EOF

}

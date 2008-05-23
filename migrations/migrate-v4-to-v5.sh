#!/bin/bash

COMMAND=$(basename $0)
BASENAME=$(basename $COMMAND .sh)
DIRNAME=$(dirname $0)

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

    sql_script=$DIRNAME/${BASENAME}.sql
    if [ -f $sql_script ] ; then
	cat $sql_script
    else
	echo Cannot locate ${BASENAME}.sql 
	echo exiting 
	exit 1
    fi
}

#!/bin/bash

COMMAND=$(basename $0)
BASENAME=$(basename $COMMAND .sh)
DIRNAME=$(dirname $0)
# normalize
DIRNAME=$(cd ${DIRNAME}; /bin/pwd)

MIGRATION_SED=$DIRNAME/${BASENAME}.sed
MIGRATION_SQL=$DIRNAME/${BASENAME}.sql
# look in ..
SCHEMA_SQL=$(dirname $DIRNAME)/planetlab5.sql

DATE=$(date +%Y-%m-%d-%H-%M)
DATE_=$(date +%Y_%m_%d_%H_%M)
LOG=${DIRNAME}/${DATE}.log
DUMP=${DIRNAME}/${DATE}-pl4.sql
RESTORE=${DIRNAME}/${DATE}-pl5.sql
FAKE=${DIRNAME}/input-pl4.sql
VIEWS_SQL=$DIRNAME/${DATE}-views5.sql

# load config
. /etc/planetlab/plc_config

# return 0 (yes) or 1 (no) whether the database exists
function check_for_database () {
    dbname=$1; shift
    psql --user=$PLC_DB_USER --quiet -c "SELECT subversion from plc_db_version LIMIT 1" $dbname > /dev/null 2>&1 
    return $?
}

# when 'service plc start' gets run, the planetlab5 DB gets created 
# so this script will drop the planetlab5 DB and re-create it from scratch 
# with the contents of the planetlab4 DB that is epxected to exist
function warning () {
    echo "$COMMAND"
    echo "This script is designed to ease the migration from myplc 4.2 to 5.0"
    echo "You can run it before of after you install a 5.0 myplc"
    echo "It will attempt to re-create the planetlab5 database from planetlab4"
    echo "The planetlab5 database is renamed, not dropped, if it is found on the system"
    echo -n "Are you sure you want to proceed y/[n] ? "
    read answer
    case $answer in
	y|Y) echo See log in $LOG ;;
	*) echo "Bye" ; exit 1 ;;
    esac
}

function check () {
    [ -f $MIGRATION_SED ] || { echo $MIGRATION_SED not found - exiting ; exit 1; }
    [ -f $MIGRATION_SQL ] || { echo $MIGRATION_SQL not found - exiting ; exit 1; }
    [ -f $SCHEMA_SQL ] || { echo $SCHEMA_SQL not found - exiting ; exit 1; }
}

function run () {
    message=$1; shift

    if [ -n "$DEBUG" ] ; then 
	echo -n "Type enter to run next step XXX $message XXX ... "
	read _answer_
    fi

    echo -n "$message "
    echo "==================================================" >> $LOG
    echo $message >> $LOG
    echo "$@" >> $LOG
    "$@" >> $LOG 2>&1
    echo Done
}

function migrate () {
    set -e
    cd $DIRNAME

    # check that planetlab4 exists
    if check_for_database planetlab4 ; then
	echo "OK : FOUND db planetlab4"
    else
	echo "ERROR : planetlab4 NOT FOUND - bye"
	exit 1
    fi

    # check if planetlab5 exists
    if check_for_database planetlab5 ; then
	rename=planetlab5_${DATE_}
	echo -n "There is an existing DB named planetlab5, drop or rename into $rename d/[r] ? "
	read _answer_
	case $_answer_ in
	    d|D)
		run "Dropping    planetlab5" psql --user=postgres template1 -c "DROP DATABASE planetlab5" || true
		;;
	    *)
		if check_for_database $rename ; then
		    echo "$rename already exists - exiting"
		    exit 1
		else
		    run "Renaming planetlab5 into $rename" \
			psql --user=postgres template1  -c "ALTER DATABASE planetlab5 RENAME TO $rename" 
		fi
		;;
	esac
    fi

    # again: now it should not exist
    if check_for_database planetlab5 ; then
	echo "ERROR : FOUND planetlab5 - should not happen - exiting"
	exit 1
    else
	echo "OK, we're clear, let's go"
    fi

    # dump planetlab4
    
    if [ ! -f $FAKE ] ; then
	run "Dumping     planetlab4 in $DUMP" pg_dump --user=$PLC_DB_USER -f $DUMP planetlab4 
    else 
	echo ''
	echo 'xxxx     WARNING     WARNING     WARNING     WARNING     WARNING     xxx'
	echo ''
	echo Using fake input for tests $FAKE
	echo ''
	echo 'xxxx     WARNING     WARNING     WARNING     WARNING     WARNING     xxx'
	echo ''
	DUMP=$FAKE
    fi

    run "Copying     into $RESTORE" cp $DUMP $RESTORE
    run "Renaming    identifiers in $RESTORE" sed -f $MIGRATION_SED -i $RESTORE

    run "Creating    planetlab5 database" createdb --user=postgres --encoding=UNICODE --owner=$PLC_DB_USER planetlab5
    run "Loading     language plpgsql" createlang -U postgres plpgsql planetlab5 || true
    run "Populating  planetlab5 from $RESTORE" psql --user=postgres -f $RESTORE planetlab5 
    run "Fine-tuning it with $MIGRATION_SQL" psql --user=$PLC_DB_USER -f $MIGRATION_SQL planetlab5
    run "Extracting  views definitions from $SCHEMA_SQL" ./extract-views.py $SCHEMA_SQL $VIEWS_SQL
    run "Inserting   views definitions in planetlab5" \
	psql --user=$PLC_DB_USER -f $VIEWS_SQL planetlab5
}

function manage_link () {
    dest=$1; shift
    src=$1; shift
    cd $DIRNAME
    echo "Managing link $dest"
    rm -f $dest
    ln -s $src $dest
}

function links () {
    # tmp 
    result=${DIRNAME}/${DATE}-output.sql
    run "Dumping result in $result" pg_dump --user=$PLC_DB_USER -f $result planetlab5

    manage_link latest.log $LOG
    manage_link latest-pl4.sql $DUMP
    manage_link latest-pl5.sql $RESTORE
    manage_link latest-views5.sql $VIEWS_SQL
    manage_link latest-output.sql $result

}

function main () {
    
    check
    warning
    set -e
    migrate
    links

}

main "$@"

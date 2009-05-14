#!/bin/bash

COMMAND=$(basename $0)
BASENAME=$(basename $COMMAND .sh)
DIRNAME=$(dirname $0)
# normalize
DIRNAME=$(cd ${DIRNAME}; /bin/pwd)

MIGRATION_SED=$DIRNAME/${BASENAME}.sed
MIGRATION_SQL=$DIRNAME/${BASENAME}.sql
# look in ..
UP=$(dirname $DIRNAME)
UPUP=$(dirname $UP)
SCHEMA_SQL=$UPUP/planetlab5.sql

DATE=$(date +%Y-%m-%d-%H-%M)
DATE_=$(date +%Y_%m_%d_%H_%M)
LOG=${DIRNAME}/${DATE}.log
DUMP=${DIRNAME}/pl4.sql
RESTORE=${DIRNAME}/${DATE}-pl5.sql
FAKE=${DIRNAME}/input-pl4.sql
VIEWS_SQL=$DIRNAME/${DATE}-views5.sql
NODEGROUPS_DEF=$DIRNAME/site-nodegroups.def
NODEGROUPS_SQL=$DIRNAME/${DATE}-nodegroups.sql

PGM_VIEWS=$UP/extract-views.py
PGM_NODEGROUPS=$DIRNAME/parse-site-nodegroups.py

INTERACTIVE_MODE="true"

# load config
. /etc/planetlab/plc_config

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

# return 0 (yes) or 1 (no) whether the database exists
function check_for_database () {
    dbname=$1; shift
    psql --user=$PLC_DB_USER --quiet -c "SELECT datname from pg_database where datname= '$dbname' LIMIT 1" $dbname > /dev/null 2>&1 
    return $?
}

# when 'service plc start' gets run, the planetlab5 DB gets created 
# so this script will drop the planetlab5 DB and re-create it from scratch 
# with the contents of the planetlab4 DB that is epxected to exist
function confirm_nodegroups () {
    echo "========================================"
    echo "$COMMAND"
    echo "This script is designed to ease the migration from myplc 4.2 to 4.3"
    echo "It attempts to (re)create the planetlab5 database from planetlab4"
    echo ""
    echo "You might wish to edit/review"
    echo "    $NODEGROUPS_DEF"
    echo "    to finetune your migration"
    echo ""
    echo "Please refer to http://svn.planet-lab.org/wiki/Migration4to5"
    echo "========================================"
    echo -n "Are you sure you want to proceed y/[n] ? "
    if [ "$INTERACTIVE_MODE" = "true" ] ; then
    	read answer
	case $answer in
	    y|Y) echo See log in $LOG ;;
	    *) echo "Bye" ; exit 1 ;;
	esac
    fi
}

function check_env () {
    [ -f $MIGRATION_SED ] || { echo $MIGRATION_SED not found - exiting ; exit 1; }
    [ -f $MIGRATION_SQL ] || { echo $MIGRATION_SQL not found - exiting ; exit 1; }
    [ -f $SCHEMA_SQL ] || { echo $SCHEMA_SQL not found - exiting ; exit 1; }
    [ -f $NODEGROUPS_DEF ] || { echo $NODEGROUPS_DEF not found - exiting ; exit 1; }
}

# connect to the former myplc, performs a local dump of planetlab4 and creates is locally
function get_planetlab4 () {

    # for faster tests ..
    if [ -f $FAKE ] ; then
	echo ''
	echo 'xxxx     WARNING     WARNING     WARNING     WARNING     WARNING     xxx'
	echo ''
	echo Using fake input for tests $FAKE
	echo ''
	echo 'xxxx     WARNING     WARNING     WARNING     WARNING     WARNING     xxx'
	echo ''
	DUMP=$FAKE
    elif [ -f $DUMP ] ; then
	echo "Using planetlab4 from $DUMP"
    else

	echo -n "Enter the hostname for the former DB service : "
	if [ "$INTERACTIVE_MODE" = "true" ] ; then 
		read hostname
		echo "Running pg_dump on $hostname.."
		pg_dump --ignore-version --host=$hostname --user=$PLC_DB_USER planetlab4 -f ${DUMP}
	else
		pg_dump --ignore-version --user=$PLC_DB_USER planetlab4 -f ${DUMP}
	fi
	DUMP=$DUMP
    fi
}

function prepare_planetlab5 () {

    # check if planetlab5 exists
    if check_for_database planetlab5 ; then
	rename=planetlab5_${DATE_}
	echo -n "There is an existing DB named planetlab5, drop or rename into $rename d/[r] ? "
	if [ "$INTERACTIVE_MODE" = "true" ] ; then
		read _answer_
	else
		_answer_='r'
	fi
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
    fi
}



function migrate () {
    set -e
    cd $DIRNAME

    # dump planetlab4
    
    run "Copying     into $RESTORE" cp $DUMP $RESTORE
    run "Renaming    identifiers in $RESTORE" sed -f $MIGRATION_SED -i $RESTORE

    run "Creating    planetlab5 database" createdb --user=postgres --encoding=UNICODE --owner=$PLC_DB_USER planetlab5
    run "Loading     language plpgsql" createlang -U postgres plpgsql planetlab5 || true
    run "Populating  planetlab5 from $RESTORE" psql --user=postgres -f $RESTORE planetlab5 
    run "Parsing     $NODEGROUPS_DEF" $PGM_NODEGROUPS $NODEGROUPS_DEF $NODEGROUPS_SQL
    run "Loading     $NODEGROUPS_SQL" psql --user=$PLC_DB_USER -f $NODEGROUPS_SQL planetlab5
    run "Fine-tuning it with $MIGRATION_SQL" psql --user=$PLC_DB_USER -f $MIGRATION_SQL planetlab5
    run "Extracting  views definitions from $SCHEMA_SQL" $PGM_VIEWS $SCHEMA_SQL $VIEWS_SQL
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

    while getopts "b" opt ; do
	case $opt in
	    b) INTERACTIVE_MODE='false' ;;
	    *) 
	    	echo "migrate.sh [-b]"
	    	echo " -b -- execute in batch mode without asking for user feedback"
		exit
	    ;;
	esac
    done
    
    check_env
    confirm_nodegroups
    echo "OK, we're clear, let's go"
    set -e
    get_planetlab4
    prepare_planetlab5
    migrate
    links
    echo "See logfile $LOG for detailed log"
    echo "Checking for 'error' in the logfile"
    grep -i error $LOG

}

main "$@"

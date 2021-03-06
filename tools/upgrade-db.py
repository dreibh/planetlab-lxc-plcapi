#!/usr/bin/env python3
#
# Tool for upgrading/converting a db
# Requirements:
# 1) Databse Schema - schema for the new database you what to upgrade to
# 2) Config File - the config file that describes how to convert the db
#
# Notes:
# 1) Will attempt to convert the db defined in  /etc/planetlab/plc_config
# 2) Does not automatically drop archived database. They must be removed
#    manually

import sys
import os
import getopt
import pgdb

config = {}
config_file = "/etc/planetlab/plc_config"
exec(compile(open(config_file).read(), config_file, 'exec'), config)
upgrade_config_file = "plcdb.3-4.conf"
schema_file = "planetlab4.sql"
temp_dir = "/tmp"


def usage():
        print("Usage: %s [OPTION] UPGRADE_CONFIG_FILE " % sys.argv[0])
        print("Options:")
        print("     -s, --schema=FILE       Upgraded Database Schema")
        print("     -t, --temp-dir=DIR      Temp Directory")
        print("     --help                  This message")
        sys.exit(1)

try:
        (opts, argv) = getopt.getopt(sys.argv[1:],
                                     "s:d:",
                                     ["schema=",
                                      "temp-dir=",
                                      "help"])
except getopt.GetoptError as err:
        print("Error: ", err.msg)
        usage()

for (opt, optval) in opts:
        if opt == "-s" or opt == "--schema":
                schema_file = optval
        elif opt == "-d" or opt == "--temp-dir":
                temp_dir = optval
        elif opt == "--help":
                usage()
try:
        upgrade_config_file = argv[0]
except IndexError:
        print("Error: too few arguments")
        usage()

schema = {}
inserts = []
schema_items_ordered = []
sequences = {}
temp_tables = {}


# load conf file for this upgrade
try:
        upgrade_config = {}
        exec(compile(open(upgrade_config_file).read(), upgrade_config_file, 'exec'), upgrade_config)
        upgrade_config.pop('__builtins__')
        db_version_previous = upgrade_config['DB_VERSION_PREVIOUS']
        db_version_new = upgrade_config['DB_VERSION_NEW']

except IOError as fault:
        print("Error: upgrade config file (%s) not found. Exiting" % \
                (fault))
        sys.exit(1) 
except KeyError as fault:
        print("Error: %s not set in upgrade confing (%s). Exiting" % \
                (fault, upgrade_config_file))
        sys.exit(1)




def connect():
        db = pgdb.connect(user = config['PLC_DB_USER'],
                  database = config['PLC_DB_NAME'])     
        return db

def archive_db(database, archived_database):

        archive_db = " dropdb -U postgres %s > /dev/null 2>&1;" \
                     " psql template1 postgres -qc " \
                     " 'ALTER DATABASE %s RENAME TO %s;';" % \
                     (archived_database, database, archived_database)
        exit_status = os.system(archive_db)
        if exit_status:
                print("Error: unable to archive database. Upgrade failed")
                sys.exit(1)
        #print "Status: %s has been archived. now named %s" % (database, archived_database)


def encode_utf8(inputfile_name, outputfile_name):
        # rewrite a iso-8859-1 encoded file in utf8
        try:
                inputfile = open(inputfile_name, 'r')
                outputfile = open(outputfile_name, 'w')
                for line in inputfile:
                        if line.upper().find('SET CLIENT_ENCODING') > -1:
                                continue
                        outputfile.write(str(line, 'iso-8859-1').encode('utf8'))
                inputfile.close()
                outputfile.close()              
        except:
                print('error encoding file')
                raise

def create_item_from_schema(item_name):

        try:
                (type, body_list) = schema[item_name]
                exit_status = os.system('psql %s %s -qc "%s" > /dev/null 2>&1' % \
                            (config['PLC_DB_NAME'], config['PLC_DB_USER'],"".join(body_list) ) )
                if exit_status:
                        raise Exception
        except Exception as fault:
                print('Error: create %s failed. Check schema.' % item_name)
                sys.exit(1)
                raise fault

        except KeyError:
                print("Error: cannot create %s. definition not found in %s" % \
                        (key, schema_file))
                return False

def fix_row(row, table_name, table_fields):

        if table_name in ['interfaces']:
                # convert str bwlimit to bps int
                bwlimit_index = table_fields.index('bwlimit')
                if isinstance(row[bwlimit_index], int):
                        pass
                elif row[bwlimit_index].find('mbit') > -1:
                        row[bwlimit_index] = int(row[bwlimit_index].split('mbit')[0]) \
                                            * 1000000
                elif row[bwlimit_index].find('kbit') > -1:
                        row[bwlimit_index] = int(row[bwlimit_index].split('kbit')[0]) \
                                             * 1000
        elif table_name in ['slice_attribute']:
                # modify some invalid foreign keys
                attribute_type_index = table_fields.index('attribute_type_id')
                if row[attribute_type_index] == 10004:
                        row[attribute_type_index] = 10016
                elif row[attribute_type_index] == 10006:
                        row[attribute_type_index] = 10017
                elif row[attribute_type_index] in [10031, 10033]:
                        row[attribute_type_index] = 10037
                elif row[attribute_type_index] in [10034, 10035]:
                        row[attribute_type_index] = 10036
        elif table_name in ['slice_attribute_types']:
                type_id_index = table_fields.index('attribute_type_id')
                if row[type_id_index] in [10004, 10006, 10031, 10033, 10034, 10035]:
                        return None
        return row
        
def fix_table(table, table_name, table_fields):
        if table_name in ['slice_attribute_types']:
                # remove duplicate/redundant primary keys
                type_id_index = table_fields.index('attribute_type_id')
                for row in table:
                        if row[type_id_index] in [10004, 10006, 10031, 10033, 10034, 10035]:
                                table.remove(row)
        return table

def remove_temp_tables():
        # remove temp_tables
        try:
                for temp_table in temp_tables:
                        os.remove(temp_tables[temp_table])
        except:
                raise

def generate_temp_table(table_name, db):
        cursor = db.cursor()
        try:
                # get upgrade directions
                table_def = upgrade_config[table_name].replace('(', '').replace(')', '').split(',')
                table_fields, old_fields, joins, wheres = [], [], set(), set()
                for field in table_def:
                        field_parts = field.strip().split(':')
                        table_fields.append(field_parts[0])
                        old_fields.append(field_parts[1])
                        if field_parts[2:]:     
                                joins.update(set([x for x in field_parts[2:] if not x.find('=') > -1]))
                                wheres.update(set([x for x in field_parts[2:] if x.find('=') > -1]))
                
                # get indices of fields that cannot be null
                (type, body_list) = schema[table_name]
                not_null_indices = []
                for field in table_fields:
                        for body_line in body_list:
                                if body_line.find(field) > -1 and \
                                   body_line.upper().find("NOT NULL") > -1:
                                        not_null_indices.append(table_fields.index(field))
                # get index of primary key
                primary_key_indices = []
                for body_line in body_list:
                        if body_line.find("PRIMARY KEY") > -1:
                                primary_key = body_line
                                for field in table_fields:
                                        if primary_key.find(" "+field+" ") > -1:
                                                primary_key_indices.append(table_fields.index(field))
                                #break
        
                # get old data
                get_old_data = "SELECT DISTINCT %s FROM %s" % \
                      (", ".join(old_fields), old_fields[0].split(".")[0])
                for join in joins:
                        get_old_data = get_old_data + " INNER JOIN %s USING (%s) " % \
                                       (join.split('.')[0], join.split('.')[1])
                if wheres:      
                        get_old_data = get_old_data + " WHERE " 
                for where in wheres:
                        get_old_data = get_old_data + " %s" % where 
                cursor.execute(get_old_data)
                rows = cursor.fetchall()

                # write data to a temp file
                temp_file_name = '%s/%s.tmp' % (temp_dir, table_name)
                temp_file = open(temp_file_name, 'w')
                for row in rows:
                        # attempt to make any necessary fixes to data
                        row = fix_row(row, table_name, table_fields)
                        # do not attempt to write null rows
                        if row == None:
                                continue
                        # do not attempt to write rows with null primary keys
                        if [x for x in primary_key_indices if row[x] == None]:
                                continue 
                        for i in range(len(row)):
                                # convert nulls into something pg can understand
                                if row[i] == None:
                                        if i in not_null_indices:
                                                # XX doesnt work if column is int type
                                                row[i] = ""
                                        else: 
                                                row[i] = "\N"
                                if isinstance(row[i], int) or isinstance(row[i], float):
                                        row[i] = str(row[i])
                                # escape whatever can mess up the data format
                                if isinstance(row[i], str):
                                        row[i] = row[i].replace('\t', '\\t')
                                        row[i] = row[i].replace('\n', '\\n')
                                        row[i] = row[i].replace('\r', '\\r')
                        data_row = "\t".join(row)
                        temp_file.write(data_row + "\n")
                temp_file.write("\.\n")
                temp_file.close()
                temp_tables[table_name] = temp_file_name

        except KeyError:
                #print "WARNING: cannot upgrade %s. upgrade def not found. skipping" % \
                #       (table_name)
                return False
        except IndexError as fault:
                print("Error: error found in upgrade config file. " \
                      "check %s configuration. Aborting " % \
                      (table_name))
                sys.exit(1)
        except:
                print("Error: configuration for %s doesnt match db schema. " \
                      " Aborting" % (table_name))
                try:
                        db.rollback()
                except:
                        pass
                raise


# Connect to current db
db = connect()
cursor = db.cursor()

# determin current db version
try:
        cursor.execute("SELECT relname from pg_class where relname = 'plc_db_version'")
        rows = cursor.fetchall()
        if not rows:
                print("Warning: current db has no version. Unable to validate config file.")
        else:
                cursor.execute("SELECT version FROM plc_db_version")
                rows = cursor.fetchall()
                if not rows or not rows[0]:
                        print("Warning: current db has no version. Unable to validate config file.")
                elif rows[0][0] == db_version_new:
                        print("Status: Versions are the same. No upgrade necessary.")
                        sys.exit()
                elif not rows[0][0] == db_version_previous:
                        print("Stauts: DB_VERSION_PREVIOUS in config file (%s) does not" \
                              " match current db version %d" % (upgrade_config_file, rows[0][0]))
                        sys.exit()
                else:
                        print("STATUS: attempting upgrade from %d to %d" % \
                                (db_version_previous, db_version_new))  
        
        # check db encoding
        sql = " SELECT pg_catalog.pg_encoding_to_char(d.encoding)" \
              " FROM pg_catalog.pg_database d " \
              " WHERE d.datname = '%s' " % config['PLC_DB_NAME']
        cursor.execute(sql)
        rows = cursor.fetchall()
        if rows[0][0] not in ['UTF8', 'UNICODE']:
                print("WARNING: db encoding is not utf8. Attempting to encode")
                db.close()
                # generate db dump
                dump_file = '%s/dump.sql' % (temp_dir)
                dump_file_encoded = dump_file + ".utf8"
                dump_cmd = 'pg_dump -i %s -U postgres -f %s > /dev/null 2>&1' % \
                           (config['PLC_DB_NAME'], dump_file)
                if os.system(dump_cmd):
                        print("ERROR: during db dump. Exiting.")
                        sys.exit(1)
                # encode dump to utf8
                print("Status: encoding database dump")
                encode_utf8(dump_file, dump_file_encoded)
                # archive original db
                archive_db(config['PLC_DB_NAME'], config['PLC_DB_NAME']+'_sqlascii_archived')
                # create a utf8 database and upload encoded data
                recreate_cmd = 'createdb -U postgres -E UTF8 %s > /dev/null; ' \
                               'psql -a -U  %s %s < %s > /dev/null 2>&1;'   % \
                          (config['PLC_DB_NAME'], config['PLC_DB_USER'], \
                           config['PLC_DB_NAME'], dump_file_encoded) 
                print("Status: recreating database as utf8")
                if os.system(recreate_cmd):
                        print("Error: database encoding failed. Aborting")
                        sys.exit(1)
                
                os.remove(dump_file_encoded)
                os.remove(dump_file)
except:
        raise


db = connect()
cursor = db.cursor()

# parse the schema user wishes to upgrade to
try:
        file = open(schema_file, 'r')
        index = 0
        lines = file.readlines()
        while index < len(lines):
                line = lines[index] 
                if line.find("--") > -1:
                        line_parts = line.split("--")
                        line = line_parts[0]
                # find all created objects
                if line.startswith("CREATE"):
                        line_parts = line.split(" ")
                        if line_parts[1:3] == ['OR', 'REPLACE']:
                                line_parts = line_parts[2:]
                        item_type = line_parts[1]
                        item_name = line_parts[2]
                        schema_items_ordered.append(item_name)
                        if item_type in ['INDEX']:
                                schema[item_name] = (item_type, line)
                        
                        # functions, tables, views span over multiple lines
                        # handle differently than indexes
                        elif item_type in ['AGGREGATE', 'TABLE', 'VIEW']:
                                fields = [line]
                                while index < len(lines):
                                        index = index + 1
                                        nextline =lines[index]
                                        if nextline.find("--") > -1:
                                                new_line_parts = nextline.split("--")
                                                nextline = new_line_parts[0]
                                        # look for any sequences
                                        if item_type in ['TABLE'] and nextline.find('serial') > -1:
                                                sequences[item_name] = nextline.strip().split()[0]
                                        fields.append(nextline)
                                        if nextline.find(";") >= 0:
                                                break
                                schema[item_name] = (item_type, fields)
                        else:
                                print("Error: unknown type %s" % item_type)
                elif line.startswith("INSERT"):
                        inserts.append(line)
                index = index + 1
                                
except:
        raise

print("Status: generating temp tables")
# generate all temp tables
for key in schema_items_ordered:
        (type, body_list) = schema[key]
        if type == 'TABLE':
                generate_temp_table(key, db)

# disconenct from current database and archive it
cursor.close()
db.close()

print("Status: archiving database")
archive_db(config['PLC_DB_NAME'], config['PLC_DB_NAME']+'_archived')
os.system('createdb -U postgres -E UTF8 %s > /dev/null; ' % config['PLC_DB_NAME'])

print("Status: upgrading database")
# attempt to create and load all items from schema into temp db
try:
        for key in schema_items_ordered:
                (type, body_list) = schema[key]
                create_item_from_schema(key)
                if type == 'TABLE':
                        if key in upgrade_config:                               
                                # attempt to populate with temp table data
                                table_def = upgrade_config[key].replace('(', '').replace(')', '').split(',')
                                table_fields = [field.strip().split(':')[0] for field in table_def]
                                insert_cmd = "psql %s %s -c " \
                                             " 'COPY %s (%s) FROM stdin;' < %s " % \
                                             (config['PLC_DB_NAME'], config['PLC_DB_USER'], key, 
                                              ", ".join(table_fields), temp_tables[key] )
                                exit_status = os.system(insert_cmd)
                                if exit_status:
                                        print("Error: upgrade %s failed" % key)
                                        sys.exit(1)
                                # update the primary key sequence
                                if key in sequences:
                                        sequence = key +"_"+ sequences[key] +"_seq"
                                        update_seq = "psql %s %s -c " \
                                             " \"select setval('%s', max(%s)) FROM %s;\" > /dev/null" % \
                                             (config['PLC_DB_NAME'], config['PLC_DB_USER'], sequence, 
                                              sequences[key], key)
                                        exit_status = os.system(update_seq)
                                        if exit_status:
                                                print("Error: sequence %s update failed" % sequence)
                                                sys.exit(1)
                        else:
                                # check if there are any insert stmts in schema for this table
                                print("Warning: %s has no temp data file. Unable to populate with old data" % key)
                                for insert_stmt in inserts:
                                        if insert_stmt.find(key) > -1:
                                                insert_cmd = 'psql %s postgres -qc "%s;" > /dev/null 2>&1' % \
                                                (config['PLC_DB_NAME'], insert_stmt)
                                                os.system(insert_cmd) 
except:
        print("Error: failed to populate db. Unarchiving original database and aborting")
        undo_command = "dropdb -U postgres %s > /dev/null; psql template1 postgres -qc" \
                       " 'ALTER DATABASE %s RENAME TO %s;';  > /dev/null" % \
                       (config['PLC_DB_NAME'], config['PLC_DB_NAME']+'_archived', config['PLC_DB_NAME'])
        os.system(undo_command) 
        #remove_temp_tables()
        raise
        
#remove_temp_tables()

print("upgrade complete")

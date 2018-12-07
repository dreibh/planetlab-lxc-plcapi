#!/usr/bin/python
#
# Tool that removes zombie records from database tables#
import sys
import os
import getopt
import pgdb
from pprint import pprint

schema_file = None
config_file = "/etc/planetlab/plc_config"
config = {}
exec(compile(open(config_file).read(), config_file, 'exec'), config)

def usage():
        print("Usage: %s SCHEMA_FILE " % sys.argv[0])
        sys.exit(1)

try:
       	schema_file  = sys.argv[1]
except IndexError:
        print("Error: too few arguments")
        usage()

# all foreing keys exist as primary kyes in another table
# will represent all foreign keys as
# { 'table.foreign_key': 'table.primary_key'} 
foreign_keys = {}
foreign_keys_ordered = []
zombie_keys = {}
# parse the schema for foreign keys
try:
        file = open(schema_file, 'r')
        index = 0
        lines = file.readlines()
        while index < len(lines):
		line = lines[index].strip()
                # find all created objects
                if line.startswith("CREATE"):
 			line_parts = line.split(" ")
			if line_parts[1:3] == ['OR', 'REPLACE']:
				line_parts = line_parts[2:]
 			item_type = line_parts[1].strip()
 			item_name = line_parts[2].strip()
			if item_type.upper() in ['TABLE']:
				while index < len(lines):
					index = index + 1
					nextline =lines[index].strip()
					if nextline.find("--") > -1:
						nextline = nextline[0:nextline.index("--")].replace(',', '')
					if nextline.upper().find("REFERENCES") > -1:
						nextline_parts = nextline.split(" ")
						foreign_key_name = nextline_parts[0].strip()
						foreign_key_table = nextline_parts[nextline_parts.index("REFERENCES")+1].strip()
						foreign_key = item_name + "."+ foreign_key_name
						primary_key = foreign_key_table +"."+ foreign_key_name 
						foreign_keys[foreign_key] = primary_key
						foreign_keys_ordered.append(foreign_key)
					elif nextline.find(";") >= 0:
                                                break
		index = index + 1
except:
	raise

db = pgdb.connect(user = config['PLC_DB_USER'],
                  database = config['PLC_DB_NAME'])
cursor = db.cursor()
try:
	for foreign_key in foreign_keys_ordered:
		primary_key = foreign_keys[foreign_key]
		sql = "SELECT distinct %s from %s"
		
		# get all foreign keys in this table
		foreign_key_parts = foreign_key.split(".")
	
		# do not delete from primary tables
		if foreign_key_parts[0] in ['addresses', 'boot_states', 'conf_files', \
			'keys', 'messages', 'nodegroups', 'interfaces', 'nodes', 'pcus', 'peers' \
                        'persons', 'roles', 'sessions', 'sites', 'slices']:
			#print "skipping table %s" % foreign_key_parts[0] 
			continue

		cursor.execute(sql % (foreign_key_parts[1], foreign_key_parts[0]))
		foreign_rows = cursor.fetchall()
				
		# get all the primary keys from this foreign key's primary table 
		primary_key_parts = primary_key.split(".")
		# foreign key name may not match primary key name. must rename these
		if primary_key_parts[1] == 'creator_person_id':
			primary_key_parts[1] = 'person_id'
		elif primary_key_parts[1] == 'min_role_id':
			primary_key_parts[1]  = 'role_id'
		sql = sql % (primary_key_parts[1], primary_key_parts[0])
		
		# determin which primary records are deleted
		desc = os.popen('psql planetlab4 postgres -c "\d %s;"' % primary_key_parts[0])
                result = desc.readlines()
		if primary_key_parts[0] in ['slices']:
			sql  = sql + " where name not like '%_deleted'"
		elif [line for line in result if line.find("deleted") > -1]:
			sql = sql + " where deleted = false"

		cursor.execute(sql)
		primary_key_rows = cursor.fetchall()
		
		# if foreign key isnt present in primay_key query, it either doesnt exist or marked as deleted
 		# also, ignore null foreign keys, not considered zombied
		zombie_keys_func = lambda key: key not in primary_key_rows and not key == [None]
		zombie_keys_list = [zombie_key[0] for zombie_key in filter(zombie_keys_func, foreign_rows)]
		print(zombie_keys_list)
		# delete these zombie records
		if zombie_keys_list:
			print(" -> Deleting %d zombie record(s) from %s after checking %s" % \
                        		(len(zombie_keys_list), foreign_key_parts[0], primary_key_parts[0]))
			sql_delete = 'DELETE FROM %s WHERE %s IN %s' % \
			(foreign_key_parts[0], foreign_key_parts[1], tuple(zombie_keys_list))
			cursor.execute(sql_delete)
			db.commit()
		#zombie_keys[foreign_key] = zombie_keys_list
	print("done")
except pgdb.DatabaseError:
	raise

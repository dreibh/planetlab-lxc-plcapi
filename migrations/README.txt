Store here migration scripts, named
<nnn>-up-<any-text>.sql
	handled as a sql script to be run against planetlab5, or
<nnn>-up-<any-text>.sh
	which is assumed to be a shell script and is run as is

Another assumption is that 
 * nnn-up-   script will set subversion number to <nnn>
 * nnn-down  script will set subversion number to <nnn>-1
 
===
See the migration script in plc.d/db for how this is used 
===

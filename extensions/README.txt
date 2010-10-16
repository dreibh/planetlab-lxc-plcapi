Create a database extension by creating a tree like follows:

- /usr/share/plc_api/extensions/<name>-up*
Contains the SQL or script that sets up the extension's database needs.
This needs to execute
INSERT INTO plc_db_extensions VALUES ('<name>', <version>);

- /usr/share/plc_api/extensions/<name>-down*
Contains the SQL or script that removes the extension from the database.

- /usr/share/plc_api/extensions/<name>/migrations/[0-9][0-9][0-9]-{up,down}-*
Migration scripts for the extension. One of the scripts for each version
has to execute
UPDATE plc_db_extensions SET version = <version> WHERE name = '<name>'

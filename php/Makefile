#
# (Re)builds PHP API. PHP classes must be defined in a single file.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
# $URL$
#

all: plc_api.php

methods.php: methods.py ../PLC/__init__.py ../PLC/Methods/__init__.py
	PYTHONPATH=.. python $< > $@
        # Indent all lines by a couple of spaces
	sed -i -e "s/^/  /" $@

plc_api.php: header.php methods.php footer.php
        # Set timestamp
	sed -e "s/@DATE@/$$(date)/" header.php > $@
	cat methods.php footer.php >> $@

clean:
	rm -f plc_api.php methods.php

.PHONY: all clean

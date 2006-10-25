#
# (Re)builds PHP API. PHP classes must be defined in a single file.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Makefile,v 1.1 2006/09/06 15:34:41 mlhuang Exp $
#

all: plcapi.php

methods.php: methods.py ../PLC/__init__.py ../PLC/Methods/__init__.py
	PYTHONPATH=.. python $< | \
	sed -e "s/^/  /" > $@

plcapi.php: header.php methods.php footer.php
	sed -e "s/@DATE@/$$(date)/" header.php | \
	cat - methods.php footer.php > $@

clean:
	rm -f plcapi.php methods.php

.PHONY: all clean

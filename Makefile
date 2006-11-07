#
# (Re)builds Python metafiles (__init__.py) and documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#
# $Id: Makefile,v 1.4 2006/11/06 22:04:58 mlhuang Exp $
#

# Metafiles
INIT := PLC/__init__.py PLC/Methods/__init__.py

# Other stuff
SUBDIRS := doc php

# autoconf compatible variables
DESTDIR := /plc/root
datadir := /usr/share
bindir := /usr/bin

all: $(INIT) $(SUBDIRS)
	python setup.py build

install:
	python setup.py install \
	    --install-purelib=$(DESTDIR)/$(datadir)/plc_api \
	    --install-scripts=$(DESTDIR)/$(datadir)/plc_api \
	    --install-data=$(DESTDIR)/$(datadir)/plc_api

$(SUBDIRS): %:
	$(MAKE) -C $@

clean:
	find . -name '*.pyc' | xargs rm -f
	rm -f $(INIT)
	for dir in $(SUBDIRS) ; do $(MAKE) -C $$dir clean ; done
	rm -rf build

index: $(INIT)

tags:
	find . '(' -name '*.py' -o -name '*.sql' -o -name '*.php' -o -name Makefile ')' | xargs etags


# All .py files in PLC/
PLC := $(filter-out %/__init__.py, $(wildcard PLC/*.py))
PLC_init := all = '$(notdir $(PLC:.py=))'.split()

PLC/__init__.py:
	echo "$(PLC_init)" >$@

ifneq ($(sort $(PLC_init)), $(sort $(shell cat PLC/__init__.py 2>/dev/null)))
PLC/__init__.py: force
endif

# All .py files in PLC/Methods/ and PLC/Methods/system/
METHODS := $(filter-out %/__init__.py, $(wildcard PLC/Methods/*.py PLC/Methods/system/*.py))
Methods_init := methods = '$(notdir $(subst system/, system., $(METHODS:.py=)))'.split()

PLC/Methods/__init__.py:
	echo "$(Methods_init)" >$@

ifneq ($(sort $(Methods_init)), $(sort $(shell cat PLC/Methods/__init__.py 2>/dev/null)))
PLC/Methods/__init__.py: force
endif

force:

.PHONY: all install force clean index tags $(SUBDIRS)

#
# (Re)builds Python metafiles (__init__.py) and documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#
# $Id: Makefile,v 1.12 2007/07/02 19:28:52 tmack Exp $
#

# Metafiles
init := PLC/__init__.py PLC/Methods/__init__.py

# Python modules
modules := psycopg2

# Temporarily until we can kill the Fedora Core 2 build
curl_vernum := $(shell printf %d 0x$(shell curl-config --vernum))
pycurl_vernum := $(shell printf %d 0x070d01) # 7.13.1
pycurl_incompatnum := $(shell printf %d 0x070f00) # 7.16.0
ifeq ($(shell test $(curl_vernum) -ge $(pycurl_vernum) && echo 1),1)
ifeq ($(shell test $(curl_vernum) -ge $(pycurl_incompatnum) && echo 0),1)
modules += pycurl
endif
endif

modules-install := $(foreach module, $(modules), $(module)-install)
modules-clean := $(foreach module, $(modules), $(module)-clean)

# Other stuff
subdirs := doc php php/xmlrpc

# autoconf compatible variables
DESTDIR := /plc/root
datadir := /usr/share
bindir := /usr/bin

PWD := $(shell pwd)

all: $(init) $(subdirs) $(modules)
	python setup.py build

install: $(modules-install)
	python setup.py install \
	    --install-purelib=$(DESTDIR)/$(datadir)/plc_api \
	    --install-scripts=$(DESTDIR)/$(datadir)/plc_api \
	    --install-data=$(DESTDIR)/$(datadir)/plc_api
	install -D -m 755 php/xmlrpc/xmlrpc.so $(DESTDIR)/$(shell php-config --extension-dir)/xmlrpc.so
	install -D -m 755 refresh-peer.py $(DESTDIR)/$(bindir)/refresh-peer.py

$(subdirs): $(init) $(modules)

$(subdirs): %:
	$(MAKE) -C $@

$(modules):
        # Install in the current directory so that we can import it while developing
	cd $@ && \
	    python setup.py build && \
	    python setup.py install_lib --install-dir=$(PWD)

$(modules-install): %-install:
	cd $* && \
	    python setup.py install_lib --install-dir=$(DESTDIR)/$(datadir)/plc_api

$(modules-clean): %-clean:
	cd $* && python setup.py clean && rm -rf build

clean: $(modules-clean)
	find . -name '*.pyc' | xargs rm -f
	rm -f $(INIT)
	for dir in $(SUBDIRS) ; do $(MAKE) -C $$dir clean ; done
	python setup.py clean && rm -rf build

index: $(init)

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

.PHONY: all install force clean index tags $(subdirs) $(modules)

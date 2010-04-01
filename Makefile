#
# (Re)builds Python metafiles (__init__.py) and documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#
# $Id$
# $URL$
#

# Metafiles - manage Legacy/ and Accessors by hand
init := PLC/__init__.py PLC/Methods/__init__.py 

# python-pycurl and python-psycopg2 avail. from fedora 5
# we used to ship our own version of psycopg2 and pycurl, for fedora4
# starting with 5.0, support for these two modules is taken out

# Other stuff - doc not implicit, it's redone by myplc-docs
subdirs := php php/xmlrpc

# autoconf compatible variables
DESTDIR := /
datadir := /usr/share
bindir := /usr/bin

PWD := $(shell pwd)

all: $(init) $(subdirs) 
	python setup.py build

install: 
	python setup.py install \
	    --install-purelib=$(DESTDIR)/$(datadir)/plc_api \
	    --install-scripts=$(DESTDIR)/$(datadir)/plc_api \
	    --install-data=$(DESTDIR)/$(datadir)/plc_api
	install -D -m 755 php/xmlrpc/xmlrpc.so $(DESTDIR)/$(shell php-config --extension-dir)/xmlrpc.so

$(subdirs): $(init)

$(subdirs): %:
	$(MAKE) -C $@

clean: 
	find . -name '*.pyc' | xargs rm -f
	rm -f $(INIT)
	for dir in $(SUBDIRS) ; do $(MAKE) -C $$dir clean ; done
	python setup.py clean && rm -rf build

index: $(init)

index-clean:
	rm $(init)

#################### regenerate indexes - not used by the build, as both files are svn added - please update as appropriate

########## PLC/
# the current content of __init__.py
PLC_now := $(sort $(shell fgrep -v '"' PLC/__init__.py 2>/dev/null))
# what should be declared
PLC_paths := $(filter-out %/__init__.py, $(wildcard PLC/*.py))
PLC_files := $(sort $(notdir $(PLC_paths:.py=)))

ifneq ($(PLC_now),$(PLC_files))
PLC/__init__.py: force
endif
PLC/__init__.py: 
	(echo '## Please use make index to update this file' ; echo 'all = """' ; cd PLC; ls -1 *.py | grep -v __init__ | sed -e 's,.py$$,,' ; echo '""".split()') > $@

########## Methods/
# the current content of __init__.py
METHODS_now := $(sort $(shell fgrep -v '"' PLC/Methods/__init__.py 2>/dev/null))
# what should be declared
METHODS_paths := $(filter-out %/__init__.py, $(wildcard PLC/Methods/*.py PLC/Methods/system/*.py))
METHODS_files := $(sort $(notdir $(subst system/, system., $(METHODS_paths:.py=))))

ifneq ($(METHODS_now),$(METHODS_files))
PLC/Methods/__init__.py: force
endif
PLC/Methods/__init__.py: 
	(echo '## Please use make index to update this file' ; echo 'native_methods = """' ; cd PLC/Methods; ls -1 *.py system/*.py | grep -v __init__ | sed -e 's,.py$$,,' -e 's,system/,system.,' ; echo '""".split()') > $@

##########

force:

.PHONY: all install force clean index tags $(subdirs)

#################### devel tools
tags:
	find . '(' -name '*.py' -o -name '*.sql' -o -name '*.php' -o -name Makefile ')' | xargs etags

.PHONY: tags

########## sync
# 2 forms are supported
# (*) if your plc root context has direct ssh access:
# make sync PLC=private.one-lab.org
# (*) otherwise, entering through the root context
# make sync PLCHOST=testplc.onelab.eu GUEST=vplc03.inria.fr

PLCHOST ?= testplc.onelab.eu

ifdef GUEST
SSHURL:=root@$(PLCHOST):/vservers/$(GUEST)
SSHCOMMAND:=ssh root@$(PLCHOST) vserver $(GUEST)
endif
ifdef PLC
SSHURL:=root@$(PLC):/
SSHCOMMAND:=ssh root@$(PLC)
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' 
RSYNC_EXCLUDES		:= --exclude .svn --exclude CVS --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(SSHURL))
	@echo "sync: You must define, either PLC, or PLCHOST & GUEST, on the command line"
	@echo "  e.g. make sync PLC=boot.planetlab.eu"
	@echo "  or   make sync PLCHOST=testplc.onelab.eu GUEST=vplc03.inria.fr"
	@exit 1
else
	+$(RSYNC) plcsh PLC planetlab5.sql migrations $(SSHURL)/usr/share/plc_api/
	+$(RSYNC) db-config.d/ $(SSHURL)/etc/planetlab/db-config.d/
	$(SSHCOMMAND) exec apachectl graceful
endif

#################### convenience, for debugging only
# make +foo : prints the value of $(foo)
# make ++foo : idem but verbose, i.e. foo=$(foo)
++%: varname=$(subst +,,$@)
++%:
	@echo "$(varname)=$($(varname))"
+%: varname=$(subst +,,$@)
+%:
	@echo "$($(varname))"


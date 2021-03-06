#
# (Re)builds Python metafiles (__init__.py) and documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#

# python-pycurl and python-psycopg2 avail. from fedora 5
# we used to ship our own version of psycopg2 and pycurl, for fedora4
# starting with 5.0, support for these two modules is taken out

# Other stuff - doc not implicit, it's redone by myplc-docs

# autoconf compatible variables
DESTDIR := /
datadir := /usr/share
bindir := /usr/bin

PWD := $(shell pwd)

all:
	python3 setup.py build

install: install-python install-phpxmlrpc

install-python:
	python3 setup.py install \
	    --install-purelib=$(DESTDIR)/$(datadir)/plc_api \
	    --install-scripts=$(DESTDIR)/$(datadir)/plc_api \
	    --install-data=$(DESTDIR)/$(datadir)/plc_api

# phpxmlrpc is a git subtree; we just ship all its contents
# under /usr/share/plc_api/php/phpxmlrpc
install-phpxmlrpc:
	mkdir -p $(DESTDIR)/$(datadir)/plc_api/php/phpxmlrpc/
	rsync --exclude .git -ai php/phpxmlrpc/ $(DESTDIR)/$(datadir)/plc_api/php/phpxmlrpc/

clean:
	find . -name '*.pyc' | xargs rm -f
	python3 setup.py clean && rm -rf build

index:
	echo "This step is obsolete"

##########

force:

.PHONY: all install force clean index tags

#################### devel tools
tags:
	find . '(' -name '*.py' -o -name '*.sql' -o -name '*.php' -o -name Makefile -o -name '[0-9][0-9][0-9]*' ')' | fgrep -v '.git/' | xargs etags

.PHONY: tags

########## sync
# 2 forms are supported
# (*) if your plc root context has direct ssh access:
# make sync PLC=private.one-lab.org
# (*) otherwise, for test deployments, use on your testmaster
# $ run export
# and cut'n paste the export lines before you run make sync

ifdef PLC
SSHURL:=root@$(PLC):/
SSHCOMMAND:=ssh root@$(PLC)
else
ifdef PLCHOSTLXC
SSHURL:=root@$(PLCHOSTLXC):/vservers/$(GUESTNAME)
SSHCOMMAND:=ssh root@$(PLCHOSTLXC) ssh -o StrictHostKeyChecking=no -o LogLevel=quiet $(GUESTHOSTNAME)
endif
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' --exclude Accessors_site.py
RSYNC_EXCLUDES		:= --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -ai $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(SSHURL))
	@echo "sync: I need more info from the command line, e.g."
	@echo "  make sync PLC=boot.planetlab.eu"
	@echo "  make sync PLCHOSTLXC=.. GUESTHOSTNAME=.. GUESTNAME=.."
	@exit 1
else
	+$(RSYNC) plcsh PLC planetlab5.sql migrations php $(SSHURL)/usr/share/plc_api/
	+$(RSYNC) db-config.d/ $(SSHURL)/etc/planetlab/db-config.d/
	+$(RSYNC) plc.d/ $(SSHURL)/etc/plc.d/
	+$(RSYNC) apache/plc.wsgi $(SSHURL)/usr/share/plc_api/apache/
	$(SSHCOMMAND) systemctl restart plc
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

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
subdirs := php/xmlrpc

# autoconf compatible variables
DESTDIR := /
datadir := /usr/share
bindir := /usr/bin

PWD := $(shell pwd)

all: $(subdirs) 
	python setup.py build

install: 
	python setup.py install \
	    --install-purelib=$(DESTDIR)/$(datadir)/plc_api \
	    --install-scripts=$(DESTDIR)/$(datadir)/plc_api \
	    --install-data=$(DESTDIR)/$(datadir)/plc_api
	install -D -m 755 php/xmlrpc/xmlrpc.so $(DESTDIR)/$(shell php-config --extension-dir)/xmlrpc.so

$(subdirs): %:
	$(MAKE) -C $@

clean: 
	find . -name '*.pyc' | xargs rm -f
	rm -f $(INIT)
	for dir in $(SUBDIRS) ; do $(MAKE) -C $$dir clean ; done
	python setup.py clean && rm -rf build

index:
	echo "This step is obsolete"

##########

force:

.PHONY: all install force clean index tags $(subdirs)

#################### devel tools
tags:
	find . '(' -name '*.py' -o -name '*.sql' -o -name '*.php' -o -name Makefile -o -name '[0-9][0-9][0-9]*' ')' | fgrep -v '.git/' | xargs etags

.PHONY: tags

########## sync
# 2 forms are supported
# (*) if your plc root context has direct ssh access:
# make sync PLC=private.one-lab.org
# (*) otherwise, under a vs-capable box, using /vservers/<> and vserver exec
# make sync PLCHOST=vs64-1.pl.sophia.inria.fr GUEST=2012.04.02--f14-32-1-vplc26
# (*) with an lxc-capable box, using /var/lib/lxc/<>/rootfs and ssh 
# make sync PLCHOSTLXC=lxc64-1.pls.sophia.inria.fr GUEST=2012.04.02--lxc16-1-vplc25

PLCHOST ?= testplc.onelab.eu

ifdef PLCHOSTLXC
VPLCNAME=$(lastword $(subst -, ,$(GUEST)))
SSHURL:=root@$(PLCHOST):/var/lib/lxc/$(GUEST)/rootfs
SSHCOMMAND:=ssh root@$(PLCHOSTLXC) ssh $(VPLCNAME)
else
ifdef GUEST
SSHURL:=root@$(PLCHOST):/vservers/$(GUEST)
SSHCOMMAND:=ssh root@$(PLCHOST) vserver $(GUEST) exec
endif
endif
ifdef PLC
SSHURL:=root@$(PLC):/
SSHCOMMAND:=ssh root@$(PLC)
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' --exclude Accessors_site.py
RSYNC_EXCLUDES		:= --exclude .svn --exclude .git --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(SSHURL))
	@echo "sync: You must define, either PLC, or PLCHOST & GUEST, on the command line"
	@echo "  e.g. make sync PLC=boot.planetlab.eu"
	@echo "  or   make sync PLCHOST=testplc.onelab.eu GUEST=vplc03.inria.fr"
	@exit 1
else
	+$(RSYNC) plcsh PLC planetlab5.sql migrations aspects $(SSHURL)/usr/share/plc_api/
	+$(RSYNC) db-config.d/ $(SSHURL)/etc/planetlab/db-config.d/
	+$(RSYNC) plc.d/ $(SSHURL)/etc/plc.d/
	$(SSHCOMMAND) apachectl graceful
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


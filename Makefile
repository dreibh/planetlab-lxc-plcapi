#
# (Re)builds Python metafiles (__init__.py) and documentation
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#
# $Id$
#

# Metafiles
init := PLC/__init__.py PLC/Methods/__init__.py

# Python modules
# see PLCAPI.spec for the settings of modules
# default is : no extra module get built

## Temporarily until we can kill the Fedora Core 2 build
#curl_vernum := $(shell printf %d 0x$(shell curl-config --vernum))
#pycurl_vernum := $(shell printf %d 0x070d01) # 7.13.1
#pycurl_incompatnum := $(shell printf %d 0x071000) # 7.16.0
#ifeq ($(shell test $(curl_vernum) -ge $(pycurl_vernum) && echo 1),1)
#ifeq ($(shell test $(curl_vernum) -ge $(pycurl_incompatnum) && echo 0),1)
#modules += pycurl
#endif
#endif

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

index-clean:
	rm $(init)

tags:
	find . '(' -name '*.py' -o -name '*.sql' -o -name '*.php' -o -name Makefile ')' | xargs etags

########## make sync PLCHOST=hostname
ifdef PLCHOST
PLCSSH:=root@$(PLCHOST)
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' 
RSYNC_EXCLUDES		:= --exclude .svn --exclude CVS --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(PLCSSH))
	echo "sync: You must define target host as PLCHOST on the command line"
	echo " e.g. make sync PLCHOST=private.one-lab.org" ; exit 1
else
	+$(RSYNC) PLC planetlab4.sql migrations $(PLCSSH):/plc/root/usr/share/plc_api/
	ssh $(PLCSSH) chroot /plc/root apachectl graceful
endif

####################
# All .py files in PLC/

# the current content of __init__.py
PLC_now := $(sort $(shell fgrep -v '"' PLC/__init__.py 2>/dev/null))
# what should be declared
PLC_paths := $(filter-out %/__init__.py, $(wildcard PLC/*.py))
PLC_files := $(sort $(notdir $(PLC_paths:.py=)))

ifneq ($(PLC_now),$(PLC_files))
PLC/__init__.py: force
endif
PLC/__init__.py: 
	(echo 'all = """' ; cd PLC; ls -1 *.py | grep -v __init__ | sed -e 's,.py$$,,' ; echo '""".split()') > $@


# the current content of __init__.py
METHODS_now := $(sort $(shell fgrep -v '"' PLC/Methods/__init__.py 2>/dev/null))
# what should be declared
METHODS_paths := $(filter-out %/__init__.py, $(wildcard PLC/Methods/*.py PLC/Methods/system/*.py))
METHODS_files := $(sort $(notdir $(subst system/, system., $(METHODS_paths:.py=))))

ifneq ($(METHODS_now),$(METHODS_files))
PLC/Methods/__init__.py: force
endif
PLC/Methods/__init__.py: 
	(echo 'methods = """' ; cd PLC/Methods; ls -1 *.py system/*.py | grep -v __init__ | sed -e 's,.py$$,,' -e 's,system/,system.,' ; echo '""".split()') > $@

force:

.PHONY: all install force clean index tags $(subdirs) $(modules)

#################### convenience, for debugging only
# make +foo : prints the value of $(foo)
# make ++foo : idem but verbose, i.e. foo=$(foo)
++%: varname=$(subst +,,$@)
++%:
	@echo "$(varname)=$($(varname))"
+%: varname=$(subst +,,$@)
+%:
	@echo "$($(varname))"


### -*-Makefile-*-
CHROOT=/plc/root
PORT=5432
SITEDIR=/etc/planetlab/configs
SITE=site.xml
RPM=$(shell ls -rt /root/myplc*rpm | tail -1)
APIDIR=/usr/share/plc_api

PLC1=lurch.cs.princeton.edu
PLC2=planetlab-devbox.inria.fr

all:help

####################
PUSH=pclean pplc1 pplc2 papi1 papi2

push:$(PUSH)

papi: pclean papi1 papi2
pplc: pclean pplc1 pplc2

pclean:
	-find . '(' -name '*.pyc' -o -name '*~' ')' | xargs rm
papi1:
	rsync -a -v -C ./ root@$(PLC1):new_plc_api/
pplc1:
	rsync -a -v -C ./PLC/ root@$(PLC1):$(CHROOT)$(APIDIR)/PLC/
	rsync -v -C ./planetlab4.sql root@$(PLC1):$(CHROOT)$(APIDIR)/planetlab4.sql
papi2:
	rsync -a -v -C ./ root@$(PLC2):new_plc_api/
pplc2:
	rsync -a -v -C ./PLC/ root@$(PLC2):$(CHROOT)$(APIDIR)/PLC/
	rsync -v -C ./planetlab4.sql root@$(PLC2):$(CHROOT)$(APIDIR)/planetlab4.sql

####################
DB=install-schema stop-clients clean-db restart
API=install-api restart

db: $(DB)

db-dump:
	chroot $(CHROOT) pg_dump -U pgsqluser planetlab4 > planetlab4.dump

api: $(API)

install-schema:
	@echo 'installing schema'
	@rsync -a -v planetlab4.sql $(CHROOT)$(APIDIR)/planetlab4.sql

install-api:
	find . -name '*.py' | xargs tar cf - | ( cd $(CHROOT)$(APIDIR) ; tar xf -)
	-find $(CHROOT)$(APIDIR) -name '*pyc' | xargs rm

stop-clients:
	@echo 'pkilling psql'
	@-pkill psql
	@echo 'pkilling Shell.py'
	@-pkill Shell.py
	@echo stopping httpd
	@chroot $(CHROOT) /etc/plc.d/httpd stop

clean-db:
	@echo 'dropping db'
	@chroot $(CHROOT) psql -U postgres --port $(PORT) template1 -c 'drop database planetlab4'

restart:
	@echo 'Restarting PLC'
	@chroot $(CHROOT) service plc restart

http:
	@echo 'Restarting httpd'
	@chroot $(CHROOT) /etc/plc.d/httpd stop ; chroot $(CHROOT) /etc/plc.d/httpd start

####################
UPGRADE=down up reconfig restart

upgrade: $(UPGRADE)

rpm:
	@echo latest rpm is $(RPM)

down:
	cp $(SITEDIR)/$(SITE) .
	rpm -e myplc
up:
	rpm -i $(RPM)

reconfig:
	service plc mount
	mkdir -p $(SITEDIR)
	cp $(SITE) $(SITEDIR)
	(echo w; echo q) | chroot $(CHROOT) plc-config-tty

####################
TEST=run checkpoint diff
run:
	python -u ./TestPeers.py > TestPeers.out 2>&1
diff:
	@echo '<< REF OUT>>'
	diff TestPeers.ref TestPeers.out 

checkpoint:
	@echo adopting latest run as reference
	cp TestPeers.out TestPeers.ref

#######
HELP=rpm db-dump http

help:
	@echo known targets:
	@echo push: $(PUSH) 
	@echo db: $(DB) 
	@echo api: $(API) 
	@echo upgrade: $(UPGRADE)
	@echo test: $(TEST)
	@echo OTHERS: $(HELP)


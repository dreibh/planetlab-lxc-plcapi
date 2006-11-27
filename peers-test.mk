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
PUSH=pclean pplc2 papi2 pplc1 papi1

push:$(PUSH)

papi: pclean papi1 papi2
pplc: pclean pplc1 pplc2

pclean:
	-find . '(' -name '*.pyc' -o -name '*~' ')' | xargs rm
papi1:
	rsync -a -v -C ./ root@$(PLC1):new_plc_api/
pplc1:
	rsync -a -v -C ./PLC/ root@$(PLC1):$(CHROOT)$(APIDIR)/PLC/
	rsync -a -v -C ./planetlab4.sql root@$(PLC1):$(CHROOT)$(APIDIR)/planetlab4.sql
papi2:
	rsync -a -v -C ./ root@$(PLC2):new_plc_api/
pplc2:
	rsync -a -v -C ./PLC/ root@$(PLC2):$(CHROOT)$(APIDIR)/PLC/
	rsync -a -v -C ./planetlab4.sql root@$(PLC2):$(CHROOT)$(APIDIR)/planetlab4.sql

####################
DB=install-schema stop-clients clean-db restart
WEB=install-api restart

db: $(DB)
	@date

db-dump:
	chroot $(CHROOT) pg_dump -U pgsqluser planetlab4 > planetlab4.dump

web: $(WEB)

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
RUN=api sql log
api:
	chroot $(CHROOT) /usr/share/plc_api/Shell.py

sql:
	chroot $(CHROOT) psql -U pgsqluser planetlab4

log:
	emacs /plc/data/var/log/httpd/error_log /plc/data/var/log/boot.log

####################
# remove time/delay dependent output
normalize	= egrep -v "'expires':|^+++.*ellapsed"

TEST=run checkpoint diff
run: run-only normalize
run-only:
	python -u ./TestPeers.py > TestPeers.out 2>&1

normalize: TestPeers.out.nor TestPeers.ref.nor
TestPeers.out.nor: TestPeers.out
	$(normalize) TestPeers.out > TestPeers.out.nor
TestPeers.ref.nor: TestPeers.ref
	$(normalize) TestPeers.ref > TestPeers.ref.nor

diff: normalize
	@echo '<< REF OUT>>'
	diff TestPeers.ref.nor TestPeers.out.nor

checkpoint:
	@echo adopting latest run as reference
	cp TestPeers.out TestPeers.ref
	cp TestPeers.out.nor TestPeers.ref.nor

frun:
	python -u ./TestPeers.py -f > TestPeers.fout 2>&1
brun:
	python -u ./TestPeers.py -b > TestPeers.bout 2>&1
prun:
	python -u ./TestPeers.py -p > TestPeers.pout 2>&1
#######
HELP=rpm db-dump http

help:
	@echo known targets:
	@echo push: $(PUSH) 
	@echo db: $(DB) 
	@echo web: $(WEB) 
	@echo upgrade: $(UPGRADE)
	@echo test: $(TEST)
	@echo run: $(RUN)
	@echo OTHERS: $(HELP)


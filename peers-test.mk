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
	rsync -a -v -C ./planetlab4.sql ./PLC root@$(PLC1):$(CHROOT)$(APIDIR)/
papi2:
	rsync -a -v -C ./ root@$(PLC2):new_plc_api/
pplc2:
	rsync -a -v -C ./planetlab4.sql ./PLC root@$(PLC2):$(CHROOT)$(APIDIR)/

####################
DB=install-schema stop-clients clean-db restart-db
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

restart-db:
	@echo 'restarting db'
	@chroot $(CHROOT) service plc stop db postgresql httpd
	@chroot $(CHROOT) service plc start httpd postgresql db

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
run: nrun normalize 
normalize: TestPeers-n.nout TestPeers-n.nref

nrun: 
	python -u ./TestPeers.py > TestPeers-n.out 2>&1
mrun:
	python -u ./TestPeers.py -m > TestPeers-m.out 2>&1
brun:
	python -u ./TestPeers.py -b > TestPeers-b.out 2>&1
prun:
	python -u ./TestPeers.py -p > TestPeers-p.out 2>&1
pbrun:
	python -u ./TestPeers.py -p -b > TestPeers-pb.out 2>&1
phrun:
	python -u ./TestPeers.py -p -H > TestPeers-ph.phout 2>&1

%.nout: %.out
	$(normalize) $*.out > $@
%.nref: %.ref
	$(normalize) $*.ref > $@

diff: normalize
	@echo '<< REF OUT>>'
	diff TestPeers-n.ref TestPeers-n.out

ckp checkpoint:
	@echo adopting latest run as reference
	cp TestPeers-n.out TestPeers-n.ref
	rm -f TestPeers-n.n???

mdiff: TestPeers-m.nref TestPeers-m.nout 
	diff TestPeers-m.nref TestPeers-m.nout
mckp:
	cp TestPeers-m.out TestPeers-m.ref
	rm -f TestPeers-m.n???

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


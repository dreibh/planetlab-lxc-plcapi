### -*-Makefile-*-
CHROOT=/plc/root
PORT=5432
SITEDIR=/etc/planetlab/configs
SITE=site.xml
RPM=$(shell ls -rt /root/myplc*rpm | tail -1)
APIDIR=/usr/share/plc_api

PLC1=lurch.cs.princeton.edu
PLC2=planetlab-devbox.inria.fr
PLC1SSH=root@$(PLC1)
PLC2SSH=root@$(PLC2)

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
DB=install-schema stop-clients db-drop restart-full-db
DBI= stop-clients db-drop restart-db db-restore restart-http
WEB=install-api restart

db: $(DB)
	@date

dbi: $(DBI)
	@echo Restored $(DBDUMP) on $(shell hostname) at $(shell date)

DBDUMP=planetlab4.dump

db-dump:
	chroot $(CHROOT) pg_dump -c -U pgsqluser planetlab4 > $(DBDUMP)

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
	service plc stop httpd

db-drop:
	echo 'dropping db'
	chroot $(CHROOT) psql -U postgres --port $(PORT) template1 -c 'drop database planetlab4'

db-restore: 
	echo Restoring $(DBDUMP)
	rm -f $(DBDUMP).rest-log  $(DBDUMP).rest-err
	chroot $(CHROOT) psql -U postgres --port $(PORT) -d planetlab4 < $(DBDUMP) > $(DBDUMP).rest-log 2> $(DBDUMP).rest-err
	ls -l $(DBDUMP).rest-log  $(DBDUMP).rest-err

restart-db:
	@echo 'restarting db only'
	service plc stop postgresql
	service plc start postgresql

restart-full-db:
	@echo 'restarting full db'
	service plc stop db postgresql httpd
	service plc start httpd postgresql db

restart:
	@echo 'Restarting PLC'
	@chroot $(CHROOT) service plc restart

restart-http:
	@echo 'Restarting httpd'
	service plc stop httpd
	service plc start httpd

####################
UPGRADE=stop-clients down clean-plc up reconfig restart

upgrade: $(UPGRADE)

rpm:
	@echo latest rpm is $(RPM)

down:
	cp $(SITEDIR)/$(SITE) .
	rpm -e myplc
clean-plc:
	rm -rf /plc
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
run: run-n normalize 
normalize: TestPeers-n.nout TestPeers-n.nref

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

# variant runs
VARIANT-TESTS :=

VARIANT-TESTS += run-n
run-n: 
	python -u ./TestPeers.py > TestPeers-n.out 2>&1
VARIANT-TESTS += run-m
run-m:
	python -u ./TestPeers.py -m > TestPeers-m.out 2>&1
VARIANT-TESTS += run-b
run-b:
	python -u ./TestPeers.py -b > TestPeers-b.out 2>&1
VARIANT-TESTS += run-p run-pn
run-p run-pn:
	python -u ./TestPeers.py -p > TestPeers-p.out 2>&1
VARIANT-TESTS += run-pb
run-pb:
	python -u ./TestPeers.py -p -b > TestPeers-pb.out 2>&1
VARIANT-TESTS += run-ph
run-ph:
	python -u ./TestPeers.py -p -H > TestPeers-ph.out 2>&1
VARIANT-TESTS += run-e run-en
run-e run-en:
	python -u ./TestPeers.py -e > TestPeers-e.out 2>&1
VARIANT-TESTS += run-eb
run-eb:
	python -u ./TestPeers.py -e -b > TestPeers-eb.out 2>&1
VARIANT-TESTS += run-eh
run-eh:
	python -u ./TestPeers.py -e -H > TestPeers-eh.out 2>&1

VARIANT-TESTS += diff-m
diff-m: TestPeers-m.nref TestPeers-m.nout 
	diff TestPeers-m.nref TestPeers-m.nout
VARIANT-TESTS += ckp-m
ckp-m:
	cp TestPeers-m.out TestPeers-m.ref
	rm -f TestPeers-m.n???

VARIANT-TESTS += diff-p
diff-p: TestPeers-p.nref TestPeers-p.nout 
	diff TestPeers-p.nref TestPeers-p.nout
VARIANT-TESTS += ckp-p
ckp-p:
	cp TestPeers-p.out TestPeers-p.ref
	rm -f TestPeers-p.n???


VARIANTS-DB := 

DB1=populate-1.sql
DB2=populate-2.sql

SAVE=save1 save2
VARIANT-DB += save
save: $(SAVE)

VARIANT-DB += save-n
save-n: DB1=populate-n-1.sql
save-n: DB2=populate-n-2.sql
save-n:save

VARIANT-DB += save-b
save-b: DB1=populate-b-1.sql
save-b: DB2=populate-b-2.sql
save-b:save

VARIANT-DB += save-h
save-h: DB1=populate-h-1.sql
save-h: DB2=populate-h-2.sql
save-h:save

save1:
	ssh $(PLC1SSH) "make -C new_plc_api -f peers-test.mk DBDUMP=$(DB1) db-dump"
	scp $(PLC1SSH):new_plc_api/$(DB1) .
save2:
	ssh $(PLC2SSH) "make -C new_plc_api -f peers-test.mk DBDUMP=$(DB2) db-dump"
	scp $(PLC2SSH):new_plc_api/$(DB2) .

RESTORE=restore1 restore2
VARIANT-DB += restore
restore:$(RESTORE)

VARIANT-DB += restore-n
restore-n: DB1=populate-n-1.sql
restore-n: DB2=populate-n-2.sql
restore-n:restore

VARIANT-DB += restore-b
restore-b: DB1=populate-b-1.sql
restore-b: DB2=populate-b-2.sql
restore-b:restore

VARIANT-DB += restore-h
restore-h: DB1=populate-h-1.sql
restore-h: DB2=populate-h-2.sql
restore-h:restore

restore1:
	scp $(DB1) $(PLC1SSH):new_plc_api/
	ssh $(PLC1SSH) "make -C  new_plc_api -f peers-test.mk DBDUMP=$(DB1) dbi"
restore2:
	scp $(DB2) $(PLC2SSH):new_plc_api/
	ssh $(PLC2SSH) "make -C  new_plc_api -f peers-test.mk DBDUMP=$(DB2) dbi"

#######
HELP=rpm db-dump restart-http

help:
	@echo known targets:
	@echo push: $(PUSH) 
	@echo db: $(DB) 
	@echo dbi: $(DBI) 
	@echo run: $(RUN)
	@echo web: $(WEB) 
	@echo upgrade: $(UPGRADE)
	@echo test: $(TEST)
	@echo other test targets: $(VARIANT-TESTS)
	@echo save:$(SAVE)
	@echo restore:$(RESTORE)
	@echo db targets: $(VARIANT-DB)
	@echo OTHERS: $(HELP)


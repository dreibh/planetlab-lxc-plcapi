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

PY=python -u

all:help

####################
PUSH=pclean pplc2 papi2 pplc1 papi1
EXTRA-PUSHS= ./Shell.py ./TestPeers.py ./planetlab4.sql ./dummy-config ./peers-test.mk ./person-password.sh

push:$(PUSH)

papi: pclean papi1 papi2
pplc: pclean pplc1 pplc2

pclean:
	-find . '(' -name '*.pyc' -o -name '*~' ')' | xargs rm
papi1:
	rsync -a -v -C ./ root@$(PLC1):new_plc_api/
pplc1:
	rsync -a -v -C $(EXTRA-PUSHS) ./PLC root@$(PLC1):$(CHROOT)$(APIDIR)/
papi2:
	rsync -a -v -C ./ root@$(PLC2):new_plc_api/
pplc2:
	rsync -a -v -C $(EXTRA-PUSHS) ./PLC root@$(PLC2):$(CHROOT)$(APIDIR)/

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

TEST=run diff checkpoint
run: run-n 

%.nout: %.out
	$(normalize) $*.out > $@
%.nref: %.ref
	$(normalize) $*.ref > $@

diff: TestPeers-n.nref TestPeers-n.nout
	@echo '<< REF OUT>>'
	diff TestPeers-n.nref TestPeers-n.nout

ckp checkpoint:
	@echo adopting latest run as reference
	cp TestPeers-n.out TestPeers-n.ref
	rm -f TestPeers-n.n???

# variant runs
VARIANT-TESTS :=

VARIANT-TESTS += run-n
run-n: 
	$(PY) ./TestPeers.py > TestPeers-n.out 2>&1
VARIANT-TESTS += run-m
run-m:
	$(PY) ./TestPeers.py -m > TestPeers-m.out 2>&1
VARIANT-TESTS += run-b
run-b:
	$(PY) ./TestPeers.py -b > TestPeers-b.out 2>&1
VARIANT-TESTS += run-p run-pn
run-pn:
	$(PY) ./TestPeers.py -p > TestPeers-pn.out 2>&1
VARIANT-TESTS += run-pb
run-pb:
	$(PY) ./TestPeers.py -p -b > TestPeers-pb.out 2>&1
VARIANT-TESTS += run-ph
run-ph:
	$(PY) ./TestPeers.py -p -H > TestPeers-ph.out 2>&1
VARIANT-TESTS += run-e run-en
run-en:
	$(PY) ./TestPeers.py -e > TestPeers-en.out 2>&1
VARIANT-TESTS += run-eb
run-eb:
	$(PY) ./TestPeers.py -e -b > TestPeers-eb.out 2>&1
VARIANT-TESTS += run-eh
run-eh:
	$(PY) ./TestPeers.py -e -H > TestPeers-eh.out 2>&1

VARIANT-TESTS += diff-m
diff-m: TestPeers-m.nref TestPeers-m.nout 
	diff TestPeers-m.nref TestPeers-m.nout
VARIANT-TESTS += ckp-m
ckp-m:
	cp TestPeers-m.out TestPeers-m.ref
	rm -f TestPeers-m.n???

VARIANT-TESTS += diff-p
diff-p: TestPeers-pn.nref TestPeers-pn.nout 
	diff TestPeers-pn.nref TestPeers-pn.nout
VARIANT-TESTS += ckp-p
ckp-p:
	cp TestPeers-pn.out TestPeers-pn.ref
	rm -f TestPeers-pn.n???

VARIANT-TESTS += diff-eh
diff-eh: TestPeers-eh.nref TestPeers-eh.nout 
	diff TestPeers-eh.nref TestPeers-eh.nout
VARIANT-TESTS += ckp-eh
ckp-eh:
	cp TestPeers-eh.out TestPeers-eh.ref
	rm -f TestPeers-eh.n???

### need to run in installed plc for gaining direct access (psycopg2 broken)
VARIANT-TESTS += run-lpn-1
run-lpn-1:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpn-1
chroot-run-lpn-1:
	$(PY) TestPeers.py -n -p -l 1 -f 8 > TestPeers-pn-1.out
VARIANT-TESTS += run-lpn-2
run-lpn-2:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpn-2
chroot-run-lpn-2:
	$(PY) TestPeers.py -n -p -l 2 -f 8 > TestPeers-pn-2.out

VARIANT-TESTS += run-lpb-1
run-lpb-1:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpb-1
chroot-run-lpb-1:
	$(PY) TestPeers.py -b -p -l 1 > TestPeers-pb-1.out
VARIANT-TESTS += run-lpb-2
run-lpb-2:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpb-2
chroot-run-lpb-2:
	$(PY) TestPeers.py -b -p -l 2 > TestPeers-pb-2.out

VARIANT-TESTS += run-lph-1
run-lph-1:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lph-1
chroot-run-lph-1:
	$(PY) TestPeers.py -H -p -l 1 > TestPeers-ph-1.out
VARIANT-TESTS += run-lph-1
run-lph-2:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lph-2
chroot-run-lph-2:
	$(PY) TestPeers.py -H -p -l 2 > TestPeers-ph-2.out


VARIANTS-DB := 

DB1=populate-1.sql
DB2=populate-2.sql

VARIANT-DB += save-n
save-n: save-n-1 save-n-2
save-n-1: DB1=populate-n-1.sql
save-n-1: save1
save-n-2: DB2=populate-n-2.sql
save-n-2:save2

VARIANT-DB += save-b
save-b: save-b-1 save-b-2
save-b-1: DB1=populate-b-1.sql
save-b-1: save1
save-b-2: DB2=populate-b-2.sql
save-b-2:save2

VARIANT-DB += save-h
save-h: save-h-1 save-h-2
save-h-1: DB1=populate-h-1.sql
save-h-1: save1
save-h-2: DB2=populate-h-2.sql
save-h-2:save2

save1:
	ssh $(PLC1SSH) make -C new_plc_api -f peers-test.mk DBDUMP=$(DB1) db-dump
	scp $(PLC1SSH):new_plc_api/$(DB1) .
save2:
	ssh $(PLC2SSH) make -C new_plc_api -f peers-test.mk DBDUMP=$(DB2) db-dump
	scp $(PLC2SSH):new_plc_api/$(DB2) .

VARIANT-DB += restore-n
restore-n: restore-n-1 restore-n-2
restore-n-1: DB1=populate-n-1.sql
restore-n-1: restore1
restore-n-2: DB2=populate-n-2.sql
restore-n-2:restore2

VARIANT-DB += restore-b
restore-b: restore-b-1 restore-b-2
restore-b-1: DB1=populate-b-1.sql
restore-b-1: restore1
restore-b-2: DB2=populate-b-2.sql
restore-b-2:restore2

VARIANT-DB += restore-h
restore-h: restore-h-1 restore-h-2
restore-h-1: DB1=populate-h-1.sql
restore-h-1: restore1
restore-h-2: DB2=populate-h-2.sql
restore-h-2:restore2

restore1:
	scp $(DB1) $(PLC1SSH):new_plc_api/
	ssh $(PLC1SSH) make -C  new_plc_api -f peers-test.mk DBDUMP=$(DB1) dbi
restore2:
	scp $(DB2) $(PLC2SSH):new_plc_api/
	ssh $(PLC2SSH) make -C  new_plc_api -f peers-test.mk DBDUMP=$(DB2) dbi

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
	@echo db targets: $(VARIANT-DB)
	@echo OTHERS: $(HELP)


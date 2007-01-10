### -*-Makefile-*-
CHROOT=/plc/root
PORT=5432
SITEDIR=/etc/planetlab/configs
SITE=site.xml
RPM=$(shell ls -rt /root/myplc*rpm | tail -1)
APIDIR=/usr/share/plc_api

PLC1=planetlab-devbox.inria.fr
PLC2=lurch.cs.princeton.edu
PLC1SSH=root@$(PLC1)
PLC2SSH=root@$(PLC2)

PY=python -u

all:help

####################
PUSH=pclean pplc1 papi1 pplc2 papi2
#EXTRA-PUSHS= ./Shell.py ./TestPeers.py ./planetlab4.sql ./dummy-config ./peers-test.mk ./person-password.sh
EXTRA-PUSHS=  ./TestPeers.py ./planetlab4.sql ./dummy-config ./peers-test.mk ./person-password.sh ./plcsh

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
DBRESTORE= stop-clients db-drop restart-db db-restore restart-http
WEB=install-api restart

db: $(DB)
	@date

dbrestore: $(DBRESTORE)
	@echo Restored $(DBDUMPFILE) on $(shell hostname) at $(shell date)

DBDUMPFILE=planetlab4.dump

db-dump:
	chroot $(CHROOT) pg_dump -c -U pgsqluser planetlab4 > $(DBDUMPFILE)

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
	echo Restoring $(DBDUMPFILE)
	rm -f $(DBDUMPFILE).rest-log  $(DBDUMPFILE).rest-err
	chroot $(CHROOT) psql -U postgres --port $(PORT) -d planetlab4 < $(DBDUMPFILE) > $(DBDUMPFILE).rest-log 2> $(DBDUMPFILE).rest-err
	ls -l $(DBDUMPFILE).rest-log  $(DBDUMPFILE).rest-err

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
PEERS= peer-gpg peer-push-gpg peer-push-cacert

peers: $(PEERS)
peer-gpg: peer-gpg-1 peer-gpg-2
peer-gpg-1:
	ssh $(PLC1SSH) "gpg --homedir=/etc/planetlab --export --armor > /etc/planetlab/gpg_plc1.pub"
peer-gpg-2:
	ssh $(PLC2SSH) "gpg --homedir=/etc/planetlab --export --armor > /etc/planetlab/gpg_plc2.pub"

# directly scp'ing from one url to the other does not work, looks like
# first host tries to connect the second one
peer-push-gpg: peer-push-gpg-1 peer-push-gpg-2
peer-push-gpg-1:
	scp $(PLC1SSH):/etc/planetlab/gpg_plc1.pub ./
	scp ./gpg_plc1.pub $(PLC2SSH):/etc/planetlab/
peer-push-gpg-2:
	scp $(PLC2SSH):/etc/planetlab/gpg_plc2.pub ./
	scp ./gpg_plc2.pub $(PLC1SSH):/etc/planetlab/

peer-push-cacert: peer-push-cacert-1 peer-push-cacert-2
peer-push-cacert-1:
	scp $(PLC1SSH):/etc/planetlab/api_ca_ssl.crt ./api_plc1.crt
	scp ./api_plc1.crt $(PLC2SSH):/etc/planetlab/
peer-push-cacert-2:
	scp $(PLC2SSH):/etc/planetlab/api_ca_ssl.crt ./api_plc2.crt
	scp ./api_plc2.crt $(PLC1SSH):/etc/planetlab/

HELP += peers-clean
peers-clean: peers-clean-1 peers-clean-2
peers-clean-1:
	ssh $(PLC1SSH) "rm -f /etc/planetlab/*plc[12]*"
peers-clean-2:
	ssh $(PLC1SSH) "rm -f /etc/planetlab/*plc[12]*"

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
	chroot $(CHROOT) /usr/bin/plcsh

sql:
	chroot $(CHROOT) psql -U pgsqluser planetlab4

log:
	emacs /plc/data/var/log/httpd/error_log /plc/data/var/log/boot.log

####################
# remove time/delay dependent output
normalize	= egrep -v "'expires':|^+++.*ellapsed"

TEST=run diff ckp
run: run-en 
diff: diff-en
ckp: ckp-en

%.nout: %.out
	$(normalize) $*.out > $@
%.nref: %.ref
	$(normalize) $*.ref > $@

# variant runs
VARIANT-TESTS :=

# run end of test (after it was populated) with normal size
VARIANT-TESTS += run-en
run-en:
	$(PY) ./TestPeers.py -e > testpeers-en.out 2>&1
# big size
VARIANT-TESTS += run-eb
run-eb:
	$(PY) ./TestPeers.py -e -b > testpeers-eb.out 2>&1
# huge size
VARIANT-TESTS += run-eh
run-eh:
	$(PY) ./TestPeers.py -e -H > testpeers-eh.out 2>&1

# normal size - performs diff and checkpoint (adopt result)
VARIANT-TESTS += diff-en
diff-en: testpeers-en.nref testpeers-en.nout 
	diff testpeers-en.nref testpeers-en.nout
VARIANT-TESTS += ckp-en
ckp-en:
	cp testpeers-en.out testpeers-en.ref
	rm -f testpeers-en.n???

VARIANT-TESTS += diff-eb
diff-eb: testpeers-eb.nref testpeers-eb.nout 
	diff testpeers-eb.nref testpeers-eb.nout
VARIANT-TESTS += ckp-eb
ckp-eb:
	cp testpeers-eb.out testpeers-eb.ref
	rm -f testpeers-eb.n???

VARIANT-TESTS += diff-eh
diff-eh: testpeers-eh.nref testpeers-eh.nout 
	diff testpeers-eh.nref testpeers-eh.nout
VARIANT-TESTS += ckp-eh
ckp-eh:
	cp testpeers-eh.out testpeers-eh.ref
	rm -f testpeers-eh.n???

### locally populate, various sizes
# need to run in installed plc for gaining direct access (psycopg2 broken)
VARIANT-TESTS += run-lpn-1
run-lpm-1:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpm-1
chroot-run-lpm-1:
	$(PY) TestPeers.py -m -p -l 1 > testpeers-pm-1.out
VARIANT-TESTS += run-lpm-2
run-lpm-2:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpm-2
chroot-run-lpm-2:
	$(PY) TestPeers.py -m -p -l 2 > testpeers-pm-2.out

VARIANT-TESTS += run-lpn-1
run-lpn-1:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpn-1
chroot-run-lpn-1:
	$(PY) TestPeers.py -p -l 1 > testpeers-pn-1.out
VARIANT-TESTS += run-lpn-2
run-lpn-2:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpn-2
chroot-run-lpn-2:
	$(PY) TestPeers.py -p -l 2 > testpeers-pn-2.out

VARIANT-TESTS += run-lpb-1
run-lpb-1:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpb-1
chroot-run-lpb-1:
	$(PY) TestPeers.py -b -p -l 1 > testpeers-pb-1.out
VARIANT-TESTS += run-lpb-2
run-lpb-2:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lpb-2
chroot-run-lpb-2:
	$(PY) TestPeers.py -b -p -l 2 > testpeers-pb-2.out

VARIANT-TESTS += run-lph-1
run-lph-1:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lph-1
chroot-run-lph-1:
	$(PY) TestPeers.py -H -p -l 1 > testpeers-ph-1.out
VARIANT-TESTS += run-lph-1
run-lph-2:
	chroot $(CHROOT) make -C $(APIDIR) -f peers-test.mk chroot-run-lph-2
chroot-run-lph-2:
	$(PY) TestPeers.py -H -p -l 2 > testpeers-ph-2.out


### old-fashioned all-in-one tests - too slow
VARIANT-TESTS += run-n
run-n: 
	$(PY) ./TestPeers.py > testpeers-n.out 2>&1
VARIANT-TESTS += run-m
run-m:
	$(PY) ./TestPeers.py -m > testpeers-m.out 2>&1
VARIANT-TESTS += diff-m
diff-m: testpeers-m.nref testpeers-m.nout 
	diff testpeers-m.nref testpeers-m.nout
VARIANT-TESTS += ckp-m
ckp-m:
	cp testpeers-m.out testpeers-m.ref
	rm -f testpeers-m.n???

### populating only, but remotely - too slow too
VARIANT-TESTS += run-p run-pn
run-pn:
	$(PY) ./TestPeers.py -p > testpeers-pn.out 2>&1
VARIANT-TESTS += run-pb
run-pb:
	$(PY) ./TestPeers.py -p -b > testpeers-pb.out 2>&1
VARIANT-TESTS += run-ph
run-ph:
	$(PY) ./TestPeers.py -p -H > testpeers-ph.out 2>&1

##############################
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
	ssh $(PLC1SSH) make -C new_plc_api -f peers-test.mk DBDUMPFILE=$(DB1) db-dump
	scp $(PLC1SSH):new_plc_api/$(DB1) .
save2:
	ssh $(PLC2SSH) make -C new_plc_api -f peers-test.mk DBDUMPFILE=$(DB2) db-dump
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
	ssh $(PLC1SSH) make -C  new_plc_api -f peers-test.mk DBDUMPFILE=$(DB1) dbrestore
restore2:
	scp $(DB2) $(PLC2SSH):new_plc_api/
	ssh $(PLC2SSH) make -C  new_plc_api -f peers-test.mk DBDUMPFILE=$(DB2) dbrestore

#######
HELP=rpm db-dump restart-http

help:
	@echo known targets:
	@echo push: $(PUSH) 
	@echo peers: $(PEERS)
	@echo db: $(DB) 
	@echo dbrestore: $(DBRESTORE) 
	@echo run: $(RUN)
	@echo web: $(WEB) 
	@echo upgrade: $(UPGRADE)
	@echo test: $(TEST)
	@echo other test targets: $(VARIANT-TESTS)
	@echo db targets: $(VARIANT-DB)
	@echo OTHERS: $(HELP)


%define name plcapi
%define version 5.4
%define taglevel 1

%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}

Summary: PlanetLab Central API
Name: %{name}
Version: %{version}
Release: %{release}
License: PlanetLab
Group: System Environment/Daemons
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab %{plrelease}
URL: %{SCMURL}

Provides: PLCAPI
Obsoletes: PLCAPI

# requirement to mod_python or mod_wsgi: deferred to myplc
Requires: httpd mod_ssl
# f29 does not come with an rpm for that; use pip instead
# Requires: Django
Requires: postgresql >= 8.2, postgresql-server >= 8.2
# We use set everywhere
Requires: python3
Requires: python3-postgresql
Requires: python3-psycopg2
Requires: python3-pycurl
# used in GPG.py as a replacement to PyXML's Canonicalize
Requires: python3-lxml
#Requires: python3-simplejson
# for the RebootNodeWithPCU method
Requires: pcucontrol >= 1.0-6
# for OMF integration - xxx aspects needs porting too
Requires: pyaspects >= 0.4
# again, these are no longer available in f29
# Requires: python-twisted-words
# Requires: python-twisted-web
# ldap
Requires: python3-ldap
# for memcache
Requires: memcached python3-memcached

####################
# obsolete
####################
# standard xmlrpc.so that ships with PHP does not marshal NULL
# prior to May 2017 we used to ship our own brew of xmlrpc but
# that does not build anymore on f25
# So bottom line is:
# * don't use fedora's php-xmlrpc (no support for marshalling NULL)
# * don't use our own that is way too old
# * instead - thank you Ciro - we pull it as a git subtree from
# https://github.com/gggeek/phpxmlrpc.git
# that stuff requires the following though
Requires: php-xml
####################


# PostgreSQL and SOAPpy are necessary to run the API server, but not
# plcsh. Since the only supported method of running the server is via
# MyPLC anyway, don't be so stringent about binary requirements, in
# case people want to install this package just for plcsh.
# Requires: postgresql-server, SOAPpy
AutoReqProv: no

%description
The PLCAPI package provides an XML-RPC and SOAP API for accessing the
PlanetLab Central (PLC) database. The API may be accessed directly via
the Python shell program plcsh, through a toy standalone server, or
through Apache mod_python.

%prep
%setup -q

%build
# python-pycurl and python-psycopg2 avail. from fedora 5
# we used to ship our own version of psycopg2 and pycurl, for fedora4
# starting with 4.3, support for these two modules is taken out
#
# Build __init__.py metafiles and PHP API.
%{__make} %{?_smp_mflags}
%{__make} -C wsdl

%install
rm -rf $RPM_BUILD_ROOT
%{__make} %{?_smp_mflags} install DESTDIR="$RPM_BUILD_ROOT" datadir="%{_datadir}" bindir="%{_bindir}"

# Install shell symlink
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
ln -s %{_datadir}/plc_api/plcsh $RPM_BUILD_ROOT/%{_bindir}/plcsh

# Install initscripts
echo "* Installing initscripts"
find plc.d | cpio -p -d -u ${RPM_BUILD_ROOT}/etc/
chmod 755 ${RPM_BUILD_ROOT}/etc/plc.d/*

# Install db-config.d files
echo "* Installing db-config.d files"
mkdir -p ${RPM_BUILD_ROOT}/etc/planetlab/db-config.d
cp db-config.d/* ${RPM_BUILD_ROOT}/etc/planetlab/db-config.d
chmod 444 ${RPM_BUILD_ROOT}/etc/planetlab/db-config.d/*

# Install wsdl
echo "* Installing wsdl"
install -D -m 644 wsdl/plcapi.wsdl $RPM_BUILD_ROOT/var/www/html/wsdl/plcapi.wsdl

## Thierry - June 2013 - omfv6 does not require xmpp pubsub nodes management any more
## Install omf_slicemgr.py
#install -D -m 755 omf/omf_slicemgr.py $RPM_BUILD_ROOT/usr/bin/omf_slicemgr.py
#install -D -m 755 omf/reset_xmpp_pubsub_nodes.py $RPM_BUILD_ROOT/usr/bin/reset_xmpp_pubsub_nodes.py
#mkdir -p $RPM_BUILD_ROOT/var/log/omf

# Create log file for plcapi
mkdir -p $RPM_BUILD_ROOT/var/log
touch $RPM_BUILD_ROOT/var/log/plcapi.log
chown apache:apache $RPM_BUILD_ROOT/var/log/plcapi.log

# Install ratelimit log
touch $RPM_BUILD_ROOT/var/log/plc_api_ratelimit.log
chown apache:apache $RPM_BUILD_ROOT/var/log/plc_api_ratelimit.log

%clean
rm -rf $RPM_BUILD_ROOT

###%define php_extension_dir %(php-config --extension-dir)

%files
%defattr(-,root,root,-)
%dir %{_datadir}/plc_api
#%dir /var/log/omf/
%{_datadir}/plc_api/*
%{_bindir}/plcsh
%config (noreplace) %{_datadir}/plc_api/PLC/Accessors/Accessors_site.py
/etc/plc.d
/etc/planetlab/db-config.d
/var/www/html/wsdl/plcapi.wsdl
#/usr/bin/omf_slicemgr.py*
#/usr/bin/reset_xmpp_pubsub_nodes.py*
/var/log/plcapi.log
/var/log/plc_api_ratelimit.log


%changelog
* Wed May 16 2018 Thierry <Parmentelat> - plcapi-5.4-1
- define accessor for site tag disabled_registration (used in plewww-5.2-9)
- set disable_existing_loggers = False in logging config, that otherwise voids sfa logs

* Sun Jul 16 2017 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.4-0
- embed phpxmlrpc as a git subtree from github (OK with fedora24 and 25, probably sooner too)
- logs in /var/log/plcapi.log
- context managers for most open files

* Wed Feb 08 2017 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-11
- mostly issued for the R2lab deployment
- *** major
- * dots allowed in login_base and slice name
- * new lease filter 'day'
- *** minor
- * more explicit message in case of overlapping resas
- * bugfix: escaping unicode in xml
- * GetLeases allowed to anonymous callers
- *** miscell
- * use plain json library

* Sun Jul 10 2016 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-10
- GetBootMedium with systemd-debug option : add kernel arg systemd.log_target=console

* Fri Jun 26 2015 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-9
- new bootstate 'upgrade' is like reinstall but leaves slices intact

* Fri Apr 24 2015 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-8
- GetBootMedium now keeps logs of created bootCD's in /var/tmp/bootmedium

* Fri Apr 03 2015 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-7
- reviewed logging strategy, no more direct print but use log instead

* Wed Feb 18 2015 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-6
- extensions for the ipv6 feature
- DeleteSliceTag can be run with the 'node' auth
- xmlrpc-epi-php.c has has a tweak for f21/php-5.6
- also SOAPpy is not present in f21 anymore, so drop that dep. with f>=21

* Tue Aug 19 2014 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-5
- allow GetSlices to filter on tags as well

* Tue Aug 19 2014 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-4
- enable filtering on tags (like hrn) with GetPersons and GetSites

* Mon Jun 02 2014 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-3
- provide more context in messages from AddPersonToSlice and DeletePersonFromSlice

* Fri Mar 21 2014 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-2
- don't use PyXML that is deprecated in f20, use lxml instead
- higher max size for login_base (32 vs 20) and slice name (64 vs 32)

* Tue Dec 10 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.3-1
- create accessor 'hrn' for site as well
- create accessors 'sfa_created' for site/slice/person
- AddSite() and AddSlice() set respectively Site HRN and Slice HRN.
- UpdatePerson() updates Person HRN according to updated email.
- UpdateSite() updates Site HRN according to updated login_base.
- Fix AddPersonToSite().
- GetPeerData() ignores Sites/Slices/Persons that have tag sfa_created=='True'
- RefreshPeer() manages Site*Person and Person*Role relationships.

* Thu Oct 10 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-10
- provide a slicename_to_hrn function

* Fri Sep 20 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-9
- add an hrn accessor for slice so the SFA code can keep track of the federation-wide name of the slice

* Wed Aug 28 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-8
- fix for wsgi-based deployments, each thread has its own api()

* Fri Jun 28 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-7
- also cleanup omf-slicemgr initscript

* Fri Jun 28 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-6
- tear down omf-related aspects as this is no longer needed with omfv6

* Thu Jun 27 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-5
- also expose 'expires' in ResolveSlices

* Wed Jun 26 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-4
- drop GetSliceSshKeys, new RetrieveSlicePersonKeys and RetrieveSliceSliverKeys

* Wed May 29 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-3
- enable netconfig aspects if PLC_NETCONFIG_ENABLED

* Wed Apr 24 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-2
- use SFA code for computing hrn's when available

* Fri Mar 08 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.2-1
- new slice tag 'interface' for configuring a virtual interface
- new builtin 030-interface_tags
- new node accessor and tag 'virt' for mixing lxc & vs nodes
- also exposed in GetNodeFlavour based on fcdistro and PLC_FLAVOUR_VIRT_MAP
- moved ModPypthon and plc.wsgi in the apache/ subdir
- renamed PLCAPI.spec into plcapi.spec
- removed old and unused tag 'type' on slices(!) - original intention seemed like virt
- support for php-5.4

* Wed Dec 19 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.1-6
- implement PLC_VSYS_DEFAULTS in AddSlice

* Wed Dec 12 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.1-5
- add hrn tag to persons, managed by AddPerson and AddPersonToSite
- AddPerson and UpdatePerson are now tag-aware
- as a side-effect AddPerson is more picky and rejects invalid fields
- which results in a requirement to use sfa-2.1-22 with this tag
- marginal improvement on the xml doc on tags

* Fri Nov 23 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.1-4
- tweak omf_slicemgr for smaller logs, split per month for easier cleaning
- reset_xmpp_pubsub_nodes now hos options and usage
- new Accessors for vicci

* Fri Aug 31 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.1-3
- fixed imports for tags management with sites and persons
- add predefined 'cpu_freezable' tag

* Mon Jul 09 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.1-2
- tweaks in interface initialization
- has 'vsys_vnet' as a predefined tagtype
- bugfix: prevent DeleteSliceFromNodes from messing with foreign slices
- bugfix: GetSlivers & nodegroups
- bugfix: in jabber groups management

* Mon Apr 16 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.1-1
- fix gpg-authentication for Persons (thanks Jordan)
- PostgreSQL.quote reviewed for f16/postgresql9 (used deprecated internal helper)
- ip address/network check: v4 or v6
- customized DB Message survive upgrade
- make sync works in lxc-hosted tests
- no svn keywords anymore

* Fri Feb 24 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-37
- fix sorting for methods list in docs
- untested but needed tweak for postgres startup in f16

* Mon Nov 28 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-36
- tweaks in postgresql setup - in line with sfa

* Mon Sep 26 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-35
- slight tweaks in Persons.py

* Wed Aug 31 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-34
- GetSession has support for more than one day sessions
- reset_xmpp_pubsub_nodes is much more efficient
- reset_xmpp_pubsub_nodes uses the config instead of localhost:5053
- bugfix - deleting a person in the middle of the signup process

* Tue Jun 07 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-33
- ratelimit aspects
- cache getslivers per node if PLC_GET_SIVERS_CACHE is enabled
- requires Django for cache_utils
- attempt to expose 'pldistro' to sfa
- last_time_spent_online, last_time_spent_offline: new fields in Node
- new slice tags 'isolate_loopback' and 'cpu_cores'
- refresh-peer federation logs dump exceptions
- modpython logs have a timestamp
- more verbose/accurate php error reporting
- postgresql listens on PLC_DB_HOST+localhost instead of 0.0.0.0
- AddNode, UpdateNode: manage tags directly rather than through another method
- BootUpdateNode: only update once
- GetPersons: techs can access the list of persons on their site
- GetSlices and GetSliceTags: techs can see slices on their nodes
- GetSlivers: isrootonsite tag; cacheable

* Tue Mar 22 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-32
- rename initscript_body into initscript_code

* Mon Mar 21 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-31
- new initscript_body tag

* Wed Mar 09 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-30
- working draft for GetSliceSshKeys

* Thu Feb 17 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-29
- trash getbootmedium tmp file if already exists but is longer than 5 minutes old
- (this is for people who cancel their download)

* Fri Feb 04 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-28
- fix db-config sequence : accessors step now merged in, and occurs at the right time
- db-config also more robust
- no more explicit 'accessors' step in plc.d

* Thu Feb 03 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-27
- session auth: do *not* delete session when node runs a method that does not have 'node' role
- session auth: remove support for bootonce in old boot CDs
- give a reason when caller_may_write_slice_tag fails
- remove ugly hack that was setting 'vref' to 'omf' - need to set both tags now

* Tue Feb 01 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-26
- SetSliceVref needed the node role
- protect GetSliceFamily
- Fix bugs in tag authorizations

* Sun Jan 23 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-25
- altered checking of optional fields in Interfaces
- UpdateTagType more picky on inputs - msg when trying to set roles, which is not supported
- has pyxml and python-simplejson as new deps

* Wed Dec 08 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-24
- tweak doc extraction for fedora14

* Tue Dec 07 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-23
- builtin accessors for the myslice page
- Get{Node,Interface}Tags allowed to techs
- tweak in ratelimitaspect.py

* Mon Dec 06 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-22
- add admin role to accessor-related tags (arch, {fc,pl}distro)

* Mon Dec 06 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-21
- bugfix in {Update,Delete}PersonTag
- updated xml doc for filters, accessors and tagtypes
- more explicit msg in case of missing roles
- improvements in ratelimitaspects.py

* Fri Dec 03 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-20
- fix the roles for ssh_key and hmac tags

* Wed Dec 01 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-19
- tag permissions system based on roles and not min_role_ids
- accessors simplified accordingly (no more min_role_id)
- new methods AddRoleToTagType and DeleteRoleFromTagType
- accessor-related tagtypes are created sooner, and enforced
- cleaned up redundancy between db-config.d and accessors

* Thu Sep 16 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-18
- fix RefreshPeer that was not working in 5.0-17

* Thu Sep 16 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-17
- RefreshPeer is able to cope with 2 peers running different releases of the api
- DeletePerson can be used on duplicates
- first appearance of ModPythonJson.py

* Wed Sep 01 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - plcapi-5.0-16
- set accessors return the new value
- tweaks in the pubsub groups management

* Wed Jul 28 2010 S.Çağlar Onur <caglar@cs.princeton.edu> - plcapi-5.0-15
- convert hostnames to lower case and use ILIKE instead of LIKE

* Fri Jul 16 2010 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - plcapi-5.0-14
- use hrn in pubsub groups

* Tue Jul 13 2010 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - plcapi-5.0-13
- Add timestamps to Nodes, PCUs and Interfaces to make concrete statements about a node's configuration state.
- OMF fixes

* Mon Jun 28 2010 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - PLCAPI-5.0-12
- automatically set vsys tag for omf controlled slices

* Sat Jun 26 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-11
- addition of the 'ssh_key' slice tag
- first draft of the LDAP interface

* Tue Jun 22 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-10
- reservation granularity defined in plc-config-tty (requires myplc 5.0.5)
- and readable through GetLeaseGranularity
- GetSlivers to expose reservation_policy and lease_granularity
- GetBootMedium fixed for reservable nodes
- tweaks in pcucontrol (requires pcucontrol-1.0-6)
- new Apache mod_wsgi python interface

* Fri May 14 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-9
- the leases system

* Wed Apr 14 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-8
- previous tag had gone wrong

* Wed Apr 14 2010 Talip Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - PLCAPI-5.0-6
- fix pubsub hostname

* Fri Apr 02 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-5
- tweaks for the omf support (xmpp groups and RC-controlled slices)
- BootNodeUpdate supports also ssh_rsa_key (and logs only changes)
- GetNodeFlavour exposes fcdistro

* Sun Mar 14 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-4
- do not use UpdateNode for handling the 'hrn' tag - should fix refresh peer & foreign nodes more generally

* Fri Mar 12 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-3
- slice tag 'omf_control' supported for getting OMF's resource controller shipped to slivers
- pyaspect hooks allow to  maintain the namespace xmpp groups
- new omf_slicemgr is a proxy to xmpp, used by these hooks
- nodes have their hrn exposed in the 'hrn' tag
- node hrn exposed in GetSlivers, as well as the overall xmpp config
- system slice 'drl' gets created by db-config
- daniel's changes to Filter for supporting wildcards in lists
- AddSliceTag consistency check tweaked

* Thu Feb 11 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-2
- major cleanup
- get rid of all 4.2-related legacy code
- reset the migrations code, planetlab5.sql somes with (5,100)
- uses hashlib module when available

* Fri Jan 29 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-1
- first working version of 5.0:
- pld.c/, db-config.d/ and nodeconfig/ scripts should now sit in the module they belong to
- nodefamily is 3-fold with pldistro-fcdistro-arch
- site and person tags
- new methods GetSliceFamily and GetNodeFlavour
- deprecated the dummynet stuff that were for the external dummyboxes
- tags definition : more consistency between db-config scripts and accessors
- (get accessor to create the tag type too if absent)
- logging an event for AddSliceToNodes

* Sat Jan 09 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-32
- support for fedora 12
- fix subtle bug in filtering with ] and quotes

* Fri Dec 18 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - PLCAPI-4.3-31
- * patch for php-5.3 (the one in f12)
- * validate email addresses with regex
- * add PersonTags and SiteTags
- * add additional accessors for node tags (kvariant, serial, ..)

* Tue Nov 03 2009 Marc Fiuczynski <mef@cs.princeton.edu> - PLCAPI-4.3-30
- Redacting password, session, and authstring values from the event log.

* Mon Oct 19 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-29
- let AddSite set ext_consortium_id - required for the poorman registration pages
- drop version constraint on Requires: postgresql-python
- don't log system calls nor ReportRunLevel

* Thu Oct 15 2009 Daniel Hokka Zakrisson <daniel@hozac.com> - PLCAPI-4.3-28
- Fix requires for CentOS.

* Fri Oct 09 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - PLCAPI-4.3-27
- Require postgresql 8.2 (for array operators && and @>)

* Thu Oct 08 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-26
- Filter now supports the | and & features to match in sequence values
- bugfix in the postgresql wrapper for sequence filter values
- reviewed GetSlivers to export admin keys more efficiently
- fix checking roles in UpdateSliceTag

* Sat Sep 26 2009 Marc Fiuczynski <mef@cs.princeton.edu> - PLCAPI-4.3-25
- - Some typos in the documentation were fixed.
- - UpdateSliceTag check if a node's min_role_id is >= (rather than >)
- to the tag's min_role_id.

* Fri Sep 18 2009 anil vengalil <avengali@sophia.inria.fr> - PLCAPI-4.3-24

* Mon Sep 07 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-23
- Ongoing work to add upcalls, using new SFA class
- new methods BindObjectToPeer, UnBindObjectFromPeer, still for SFA
- reviewed type-checking for the 3 taggable classes node-interface-slice
- cleanup ald dummynet stuff
- expose the 'extensions' accessors to the API
- tweaked checks in AddSliceTag
- GetPersons exposes roles by default
- bugfix in ReportRunLevel for non-string levels
- tweaks in GetSlivers ( seems that it now exposes the keys for the root context )

* Fri Jul 10 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-22
- new BindObjectToPeer method for sfa
- AddSliceTag and UpdateSliceTag open to the 'node' auth method with restrictions

* Wed Jul 01 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-21
- getbootmedium supports options as tags (serial, cramfs, kvariant, kargs, no-hangcheck )
- reportrunlevel logs its calls only when run_level changes
- pycurl more robust wrt to xmlrpclib.Transport

* Tue Jun 16 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-20
- produce a wsdl interface
- bugfix in getbootmedium for nodes with interface tags

* Sun Jun 07 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-19
- bugfix for some rare pattern-based filters

* Wed Jun 03 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-18
- improvements in the 4.2 legacy layer

* Sat May 30 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-17
- bugfix required for slice tags set on nodegroups

* Thu May 28 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-16
- more complete compatibility layer - second iteration, with legacy code isolated in Legacy/

* Tue May 26 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-15
- more powerful legacy layer with 4.2

* Fri May 15 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-14
- RefreshPeer sets lock per-peer to avoid multiple concurent instances
- migration script has an option for running interactively

* Wed May 06 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-13
- skips already added entries

* Tue Apr 28 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-12
- yet another set of fixes for external dummynet boxes

* Wed Apr 22 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-11
- GetDummyBoxMedium returns a base64-encoded boot image, doc is updated
- and tmp file is cleaned up

* Wed Apr 22 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-10
- restore missing ResolveSlices

* Mon Apr 20 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-9
- new method GetDummyBoxMedium

* Fri Apr 17 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-8
- remove duplicate in Methods/__init__ that was breaking build of myplc-docs

* Fri Apr 17 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-7
- support for external dummynet boxes back in 4.3 - first draft

* Thu Apr 09 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-6
- fixes for smooth federation between 4.2 and 4.3
- peername is not UNIQUE in schema anymore, was preventing delete/recreate

* Tue Apr 07 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-5
- support for BootCD variants (GetBootMedium ['variant:centos5'])
- fix corner case with filters like {'~slice_id':[]}
- fix transaction leak that caused the db connections pool to exhaust
- properly expose all methods, including Legacy/, and not only Methods/

* Tue Mar 24 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-4
- renumbered as 4.3
- nodes have new fields run_level (in addition to boot_state) and verified
- tweaked migration from 4.2
- tuned rpm dependencies
- doc generation more explicit about errors like missing python modules
- removed obsolete method GetSlicesMD5

* Wed Jan 28 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-3
- unified all tags
- renamed interface settings into interface tags and slice attributes into slice tags
- nodes have a node_type
- various changes on the way to 4.3

* Thu Nov 27 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-2
- Checkpointing : this version still has interface settings and slice attributes

* Wed Sep 10 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.3-1
- first iteration with taggable nodes/interfaces/slices
- embryo for ilinks
- cleaned up boot states
- migration script moslty complete

* Wed May 14 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.2-8
- fixed doc build by locating locally installed DTDs at build-time

* Fri May 09 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.2-7
- no more doc packaged outside of myplc-docs - doc/ cleaned up
- enhancements in doc on filters
- bootcd-aware GetBootMedium merged from onelab

* Thu May 08 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.2-6
- checkpoint while the new myplc-docs package is underway
- bugfix: GetSlivers & conf files
- doc: removed target files

* Wed Apr 23 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - PLCAPI-4.2-5
- Removed conditions on the persons, site, and nodes indexes.  previsouly only
- the non-deleted fields were index, resulting in massivly slow queries.
-

* Wed Mar 26 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.2-3 PLCAPI-4.2-4
- plcsh: better handling of options when running as a shell script
- getbootmedium exports compute_key
- tweaks for accepted args in GetPCUTypes and BootNotifyOwners

* Thu Feb 14 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.2-2 PLCAPI-4.2-3
- GetBootMedium support for build.sh full options, incl. serial & console_spec
- GetBootMedium simpler, cleaner and safer use of tmpdirs in (dated from bootcustom.sh)

* Fri Feb 01 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.2-1 PLCAPI-4.2-2
- refresh peer script to use a month-dependent logfile
- tracking the starting point for UniPi integration of the dummynet boxes

* Thu Jan 31 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-4.2-0 PLCAPI-4.2-1
- plcsh adds its own path to sys.path
- fix so GetNodes can be called from a Node

* Fri Oct 27 2006 Mark Huang <mlhuang@CS.Princeton.EDU> -
- Initial build.

%define module_current_branch 4.3

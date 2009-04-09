#
# $Id$
#

%define url $URL$

%define name PLCAPI
%define version 4.3
%define taglevel 6

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
URL: %(echo %{url} | cut -d ' ' -f 2)

Obsoletes: plcapilib

# We use set everywhere
Requires: python >= 2.4
Requires: postgresql postgresql-server postgresql-python
Requires: python-psycopg2
Requires: python-pycurl
Requires: httpd
Requires: mod_python
Requires: mod_ssl
Requires: SOAPpy

# We use psycopg2
BuildRequires: postgresql-devel

# Standard xmlrpc.so that ships with PHP does not marshal NULL
BuildRequires: php-devel
Obsoletes: php-xmlrpc
Provides: php-xmlrpc

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

%install
rm -rf $RPM_BUILD_ROOT
%{__make} %{?_smp_mflags} install DESTDIR="$RPM_BUILD_ROOT" datadir="%{_datadir}" bindir="%{_bindir}"

# Install shell symlink
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
ln -s %{_datadir}/plc_api/plcsh $RPM_BUILD_ROOT/%{_bindir}/plcsh

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/php.d
cat > $RPM_BUILD_ROOT/%{_sysconfdir}/php.d/xmlrpc.ini <<EOF
; Enable xmlrpc extension module
extension=xmlrpc.so
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%define php_extension_dir %(php-config --extension-dir)

%files
%defattr(-,root,root,-)
%dir %{_datadir}/plc_api
%{_datadir}/plc_api/*
%{_bindir}/plcsh
%{php_extension_dir}/xmlrpc.so
%{_sysconfdir}/php.d/xmlrpc.ini
%config (noreplace) %{_datadir}/plc_api/PLC/Accessors/Accessors_site.py

%changelog
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

%define module_current_branch 4.2

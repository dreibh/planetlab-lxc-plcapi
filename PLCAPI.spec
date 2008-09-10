#
# $Id$
#

%define url $URL$

%define name PLCAPI
%define version 5.0
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
URL: %(echo %{url} | cut -d ' ' -f 2)

Obsoletes: plcapilib

# We use set everywhere
Requires: python >= 2.4

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
# starting with 5.0, support for these two modules is taken out
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
* Wed Sep 10 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - PLCAPI-5.0-1
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

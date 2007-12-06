#
# $Id$
#

%define url $URL$

%define name PLCAPI
%define version 4.2
%define subversion 0

%define release %{subversion}%{?pldistro:.%{pldistro}}%{?date:.%{date}}

Summary: PlanetLab Central API
Name: %{name}
Version: %{version}
Release: %{release}
License: PlanetLab
Group: System Environment/Daemons
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
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

# OpenJade does not honor XML catalog files and tries to access
# www.oasis-open.org even if DTDs are locally installed. Disable
# documentation generation for now.
# BuildRequires: docbook-dtds, docbook-utils-pdf

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
# make sure to check build/<pldistro>/plc.pkgs
if [ "%{distrorelease}" -le 4 ] ; then
    modules="psycopg2 pycurl"
else
    modules=""
fi
# Build __init__.py metafiles and PHP API. 
%{__make} %{?_smp_mflags} subdirs="php php/xmlrpc" modules="$modules"
# Build documentation
# beware that making the pdf file somehow overwrites the html
%{__make} -C doc PLCAPI.pdf
rm -f doc/PLCAPI.html
%{__make} -C doc PLCAPI.html

%install
rm -rf $RPM_BUILD_ROOT
%{__make} %{?_smp_mflags} install DESTDIR="$RPM_BUILD_ROOT" datadir="%{_datadir}" bindir="%{_bindir}"
#someone out there skips doc installation - we DO want this installed
for doc in PLCAPI.html PLCAPI.pdf ; do
    install -D -m 644 doc/$doc $RPM_BUILD_ROOT/"%{_datadir}"/plc_api/doc/$doc
done

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
#someone out there skips doc installation - we DO want this installed
#%doc doc/PLCAPI.xml doc/PLCAPI.pdf doc/PLCAPI.html
%dir %{_datadir}/plc_api
%{_datadir}/plc_api/*
%{_bindir}/plcsh
%{php_extension_dir}/xmlrpc.so
%{_sysconfdir}/php.d/xmlrpc.ini
%{_bindir}/refresh-peer.py*

%changelog
* Fri Oct 27 2006 Mark Huang <mlhuang@CS.Princeton.EDU> - 
- Initial build.

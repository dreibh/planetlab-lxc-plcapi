Summary: PlanetLab Central API
Name: PLCAPI
Version: 4.0
Release: 1%{?pldistro:.%{pldistro}}%{?date:.%{date}}
License: PlanetLab
Group: System Environment/Daemons
URL: http://cvs.planet-lab.org/cvs/new_plc_api
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

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

Requires: postgresql-server, SOAPpy

%description
The PLCAPI package provides an XML-RPC and SOAP API for accessing the
PlanetLab Central (PLC) database. The API may be accessed directly via
the Python shell program plcsh, through a toy standalone server, or
through Apache mod_python.

%prep
%setup -q

%build
# Build __init__.py metafiles and PHP API. Do not build documentation
# for now.
%{__make} %{?_smp_mflags} SUBDIRS="php php/xmlrpc"

%install
rm -rf $RPM_BUILD_ROOT
%{__make} %{?_smp_mflags} install DESTDIR="$RPM_BUILD_ROOT" datadir="%{_datadir}" bindir="%{_bindir}"

# Install shell symlink
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
ln -s %{_datadir}/plc_api/Shell.py $RPM_BUILD_ROOT/%{_bindir}/plcsh

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
%doc doc/PLCAPI.xml doc/PLCAPI.pdf doc/PLCAPI.html
%dir %{_datadir}/plc_api
%{_datadir}/plc_api/*
%{_bindir}/plcsh
%{php_extension_dir}/xmlrpc.so
%{_sysconfdir}/php.d/xmlrpc.ini

%changelog
* Fri Oct 27 2006 Mark Huang <mlhuang@CS.Princeton.EDU> - 
- Initial build.


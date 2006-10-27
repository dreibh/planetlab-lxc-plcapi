Summary: PlanetLab Central API
Name: PLCAPI
Version: 4.0
Release: 1
License: PlanetLab
Group: System Environment/Daemons
URL: http://cvs.planet-lab.org/cvs/new_plc_api
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

Obsoletes: plcapilib

BuildRequires: docbook-dtds, docbook-utils-pdf

Requires: postgresql-server, SOAPpy

%description
The PLCAPI package provides an XML-RPC and SOAP API for accessing the
PlanetLab Central (PLC) database. The API may be accessed directly via
the Python shell program plcsh, through a toy standalone server, or
through Apache mod_python.

%prep
%setup -q

%build
# Build __init__.py metafiles, documentation, and PHP API
%{__make} %{?_smp_mflags}

# Byte compile
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT

# Install in /usr/share/plc_api
%{__python} setup.py install \
    --install-purelib=$RPM_BUILD_ROOT/%{_datadir}/plc_api \
    --install-scripts=$RPM_BUILD_ROOT/%{_datadir}/plc_api \
    --install-data=$RPM_BUILD_ROOT/%{_datadir}/plc_api

# Install shell symlink
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
ln -s %{_datadir}/plc_api/Shell.py $RPM_BUILD_ROOT/%{_bindir}/plcsh

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc doc/PLCAPI.xml doc/PLCAPI.pdf doc/PLCAPI.html
%dir %{_datadir}/plc_api
%{_datadir}/plc_api/*
%{_bindir}/plcsh

%changelog
* Fri Oct 27 2006 Mark Huang <mlhuang@CS.Princeton.EDU> - 
- Initial build.


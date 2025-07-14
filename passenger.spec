#
# Conditional build:
%bcond_with	tests		# test target

Summary:	A module to bridge Ruby on Rails to Apache
Summary(pl.UTF-8):	Moduł służący za bramkę Ruby on Rails do Apache'a
Name:		passenger
Version:	6.0.20
Release:	0.1
# Passenger code uses MIT license.
# Bundled(Boost) uses Boost Software License
# BCrypt and Blowfish files use BSD license.
# Documentation is CC-BY-SA
# See: https://bugzilla.redhat.com/show_bug.cgi?id=470696#c146
License:	Boost and BSD and BSD with advertising and MIT and zlib
Group:		Networking/Daemons/HTTP
Source0:	https://github.com/phusion/passenger/archive/release-%{version}.tar.gz
# Source0-md5:	1f94d1264e6fdbe5a202472454e00d88
Source1:	apache-mod_%{name}.conf
Patch0:		alias+public.patch
Patch1:		no-bundler.patch
URL:		https://www.phusionpassenger.com/
BuildRequires:	apache-devel >= 2.0.55-1
BuildRequires:	apache-tools
BuildRequires:	apr-devel >= 1:1.0.0
BuildRequires:	apr-util-devel >= 1:1.0.0
#BuildRequires:	asciidoc
BuildRequires:	curl-devel
BuildRequires:	libev-devel >= 4.11
BuildRequires:	libstdc++-devel
BuildRequires:	libuv-devel >= 1.4.2
BuildRequires:	openssl-devel
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.559
BuildRequires:	ruby-devel
BuildRequires:	ruby-rake >= 0.8.0
BuildRequires:	ruby-rdoc
BuildRequires:	sed >= 4.0
BuildRequires:	zlib-devel
%if %(locale -a | grep -q '^en_US$'; echo $?)
BuildRequires:	glibc-localedb-all
%endif
Obsoletes:	apache-mod_rails-rdoc
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		apxs		/usr/sbin/apxs
%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		_sysconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)/conf.d

%description
Phusion Passenger - a.k.a. mod_passenger - makes deployment of
applications built on the revolutionary Ruby on Rails web framework a
breeze. It follows the usual Ruby on Rails conventions, such as
"Don't-Repeat-Yourself".

%description -l pl.UTF-8
Phusion Passenger (inaczej mod_passenger) ułatwia wdrażanie aplikacji
zbudowanych w oparciu o rewolucyjny szkielet WWW Ruby on Rails. Jest
zgodny ze zwyczajowymi konwencjami Ruby on Rails, takimi jak "nie
powtarzaj się".

%package -n apache-mod_passenger
Summary:	Apache Module for Phusion Passenger
Summary(pl.UTF-8):	Moduł Apache'a dla Phusion Passengera
License:	Boost and BSD and BSD with advertising and MIT and zlib
Group:		Daemons
Requires:	%{name} = %{version}-%{release}
Requires:	apache(modules-api) = %apache_modules_api
Requires:	ruby-bundler
Provides:	apache(mod_passenger)
Provides:	apache(mod_rails)
Obsoletes:	apache-mod_rails < 4.0

%description -n apache-mod_passenger
This package contains the pluggable Apache server module for Phusion
Passenger.

%description -n apache-mod_passenger -l pl.UTF-8
Ten pakiet zawiera ładowalny moduł serwera Apache dla Phusion
Passengera.

%package -n ruby-passenger-ri
Summary:	ri documentation for Phusion Passenger
Summary(pl.UTF-8):	Dokumentacja w formacie ri dla Phusion Passengera
Group:		Documentation
Requires:	ruby
Obsoletes:	apache-mod_rails-ri < 4.0

%description -n ruby-passenger-ri
ri documentation for Phusion Passenger.

%description -n ruby-passenger-ri -l pl.UTF-8
Dokumentacji w formacie ri dla Phusion Passengera.

%prep
%setup -q -n %{name}-release-%{version}
#%patch0 -p1
%patch -P1 -p1

%{__sed} -i -e 's|#!/usr/bin/env python|#!%{_bindir}/python3|' src/helper-scripts/*.py
%{__sed} -i -e 's|#!/usr/bin/env ruby|#!%{_bindir}/ruby|' src/helper-scripts/{prespawn,download_binaries/extconf.rb,*.rb} bin/*

# Don't use bundled libs
%{__rm} -r src/cxx_supportlib/vendor-modified/libev
%{__rm} -r src/cxx_supportlib/vendor-copy/libuv

%build
export USE_VENDORED_LIBEV=no
export USE_VENDORED_LIBUV=no
export CC="%{__cc}"
export CXX="%{__cxx}"
export CFLAGS="%{rpmcflags} -fno-strict-aliasing"
export CXXFLAGS="%{rpmcxxflags} -fno-strict-aliasing"
export EXTRA_CFLAGS="%{rpmcflags} -fno-strict-aliasing"
export EXTRA_CXXFLAGS="%{rpmcxxflags} -fno-strict-aliasing"
export EXTRA_PRE_LDFLAGS="%{rpmldflags}"

export APACHECTL=%{_sbindir}/apachectl
export HTTPD_VERSION=$(rpm -q apache-devel --qf '%{V}')
export HTTPD=%{_sbindir}/httpd
export APXS2=%{apxs}

rake apache2 V=1 \
	NATIVE_PACKAGING_METHOD=rpm \
	FS_PREFIX=%{_prefix} \
	FS_BINDIR=%{_bindir} \
	FS_SBINDIR=%{_sbindir} \
	FS_DATADIR=%{_datadir} \
	FS_LIBDIR=%{_libdir} \
	RUBYLIBDIR=%{ruby_vendorlibdir} \
	RUBYARCHDIR=%{_libdir}/%{name} \
	APACHE2_MODULE_PATH=%{_libdir}/apache/mod_passenger.so
	RELEASE=yes \
	OPTIMIZE=yes

%if %{with tests}
# Run the tests, capture the output, but don't fail the build if the tests fail
#
# This will make the test failure non-critical, but it should be examined
# anyway.
%{__sed} -i 's|sh "cd test && \./cxx/CxxTestMain"|& rescue true|' build/cxx_tests.rb

# adjust for rspec 2 while the test suite seems to require RSpec 1.
%{__sed} -i \
	"s|return locate_ruby_tool('spec')|return locate_ruby_tool('rspec')|" \
	lib/phusion_passenger/platform_info/ruby.rb

rake test --trace
%endif

# UTF8 locale needed for doc generation
LC_ALL=en_US.UTF-8 \
rdoc --ri --op ri lib ext/ruby
%{__rm} -r ri/{GC,IO,Object,Signal,CommonLibraryBuilder,Exception}
%{__rm} ri/{cache.ri,created.rid}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir},%{_mandir}/man{1,8}} \
	$RPM_BUILD_ROOT{%{ruby_vendorlibdir},%{ruby_vendorarchdir},%{ruby_ridir}/PhusionPassenger} \
	$RPM_BUILD_ROOT%{_bindir} \
	$RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents/apache2 \
	$RPM_BUILD_ROOT%{_datadir}/phusion-passenger/{node_lib,helper-scripts}

install -p buildout/apache2/mod_passenger.so $RPM_BUILD_ROOT%{_pkglibdir}
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/75_mod_passenger.conf

install -p buildout/ruby/ruby-*/passenger_native_support.so $RPM_BUILD_ROOT%{ruby_vendorarchdir}
cp -a src/ruby_supportlib/* $RPM_BUILD_ROOT%{ruby_vendorlibdir}

install -p bin/passenger-{config,memory-stats,status} bin/passenger $RPM_BUILD_ROOT%{_bindir}
#install -p buildout/agents/{PassengerLoggingAgent,PassengerWatchdog,PassengerHelperAgent,SpawnPreparer,TempDirToucher} $RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents
cp -a src/helper-scripts/* $RPM_BUILD_ROOT%{_datadir}/phusion-passenger/helper-scripts
cp -a resources $RPM_BUILD_ROOT%{_datadir}/phusion-passenger/
# does that make any sense?
cp -a src/nodejs_supportlib/phusion_passenger/*.js $RPM_BUILD_ROOT%{_datadir}/phusion-passenger/node_lib

cp -p man/*.1 $RPM_BUILD_ROOT%{_mandir}/man1
cp -p man/*.8 $RPM_BUILD_ROOT%{_mandir}/man8
cp -a ri/* $RPM_BUILD_ROOT%{ruby_ridir}/PhusionPassenger

%clean
rm -rf $RPM_BUILD_ROOT

%post -n apache-mod_passenger
%service -q httpd restart

%postun -n apache-mod_passenger
if [ "$1" = "0" ]; then
	%service -q httpd restart
fi

%files
%defattr(644,root,root,755)
%doc README.md INSTALL.md
%attr(755,root,root) %{_bindir}/passenger
%attr(755,root,root) %{_bindir}/passenger-config
%attr(755,root,root) %{_bindir}/passenger-memory-stats
%attr(755,root,root) %{_bindir}/passenger-status
%{_mandir}/man1/passenger-config.1*
%{_mandir}/man8/passenger-memory-stats.8*
%{_mandir}/man8/passenger-status.8*
%attr(755,root,root) %{ruby_vendorarchdir}/passenger_native_support.so
%{ruby_vendorlibdir}/phusion_passenger.rb
%{ruby_vendorlibdir}/phusion_passenger

%dir %{_libdir}/phusion-passenger
%dir %{_libdir}/phusion-passenger/agents
#%attr(755,root,root) %{_libdir}/phusion-passenger/agents/PassengerHelperAgent
#%attr(755,root,root) %{_libdir}/phusion-passenger/agents/PassengerLoggingAgent
#%attr(755,root,root) %{_libdir}/phusion-passenger/agents/PassengerWatchdog
#%attr(755,root,root) %{_libdir}/phusion-passenger/agents/SpawnPreparer
#%attr(755,root,root) %{_libdir}/phusion-passenger/agents/TempDirToucher
%dir %{_datadir}/phusion-passenger
%dir %{_datadir}/phusion-passenger/helper-scripts
%attr(755,root,root) %{_datadir}/phusion-passenger/helper-scripts/*
%{_datadir}/phusion-passenger/resources
%{_datadir}/phusion-passenger/node_lib

%files -n apache-mod_passenger
%defattr(644,root,root,755)
%defattr(644,root,root,755)
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/*_mod_passenger.conf
%attr(755,root,root) %{_pkglibdir}/mod_passenger.so

%files -n ruby-passenger-ri
%defattr(644,root,root,755)
%{ruby_ridir}/PhusionPassenger

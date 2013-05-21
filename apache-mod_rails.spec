#
# Conditional build:
%bcond_with	tests		# build without tests

%define		gem_name	passenger
Summary:	A module to bridge Ruby on Rails to Apache
Name:		apache-mod_rails
Version:	3.0.19
Release:	1
# Passenger code uses MIT license.
# Bundled(Boost) uses Boost Software License
# BCrypt and Blowfish files use BSD license.
# Documentation is CC-BY-SA
# See: https://bugzilla.redhat.com/show_bug.cgi?id=470696#c146
License:	Boost and BSD and BSD with advertising and MIT and zlib
Group:		Networking/Daemons/HTTP
Source0:	https://github.com/FooBarWidget/passenger/archive/release-%{version}.tar.gz
# Source0-md5:	de848f42cb4f83e19d6c8a41a187a4db
Source1:	%{name}.conf
Patch0:		%{name}-nogems.patch
Patch1:		%{name}-alias+public.patch
Patch2:		passenger_apache_fix_autofoo.patch
Patch3:		progs.patch
URL:		http://www.modrails.com/
BuildRequires:	apache-devel >= 2.0.55-1
BuildRequires:	apr-devel >= 1:1.0.0
BuildRequires:	apr-util-devel >= 1:1.0.0
#BuildRequires:	asciidoc
BuildRequires:	curl-devel
BuildRequires:	libev-devel
BuildRequires:	libstdc++-devel
BuildRequires:	openssl-devel
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.559
BuildRequires:	ruby-devel
BuildRequires:	ruby-rake >= 0.8.0
BuildRequires:	ruby-rdoc
BuildRequires:	sed >= 4.0
BuildRequires:	zlib-devel
Requires:	apache(modules-api) = %apache_modules_api
Provides:	apache(mod_rails)
Obsoletes:	apache-mod_rails-rdoc
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		apxs		/usr/sbin/apxs
%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		_sysconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)/conf.d

%description
Phusion Passenger — a.k.a. mod_rails — makes deployment of
applications built on the revolutionary Ruby on Rails web framework a
breeze. It follows the usual Ruby on Rails conventions, such as
"Don’t-Repeat-Yourself".

%package ri
Summary:	ri documentation for Apache mod_rails
Summary(pl.UTF-8):	Dokumentacja w formacie ri dla Apache mod_rails
Group:		Documentation
Requires:	ruby

%description ri
ri documentation for Apache mod_rails.

%description ri -l pl.UTF-8
Dokumentacji w formacie ri dla Apache mod_rails.

%prep
%setup -q -n %{gem_name}-release-%{version}
%patch0 -p1
%patch1 -p0
%patch2 -p0
%patch3 -p1

mv test/config.yml{.example,}

# Don't use bundled libev
rm -r ext/libev

%build
export USE_VENDORED_LIBEV=false
export CC="%{__cc}"
export CXX="%{__cxx}"
export CFLAGS="%{rpmcflags}"
export CXXFLAGS="%{rpmcxxflags}"
export APACHECTL=%{_sbindir}/apachectl
export HTTPD_VERSION=$(rpm -q apache-devel --qf '%{V}')

rake apache2 V=1 \
	RELEASE=yes \
	OPTIMIZE=yes \
	HTTPD=false

%if %{with tests}
# Run the tests, capture the output, but don't fail the build if the tests fail
#
# This will make the test failure non-critical, but it should be examined
# anyway.
sed -i 's|sh "cd test && \./cxx/CxxTestMain"|& rescue true|' build/cxx_tests.rb

# adjust for rspec 2 while the test suite seems to require RSpec 1.
sed -i \
	"s|return locate_ruby_tool('spec')|return locate_ruby_tool('rspec')|" \
	lib/phusion_passenger/platform_info/ruby.rb

rake test --trace
%endif

rdoc --ri --op ri lib ext/ruby
%{__rm} -r ri/{ConditionVariable,Exception,GC,IO,Object,Process,Signal}
%{__rm} ri/{cache.ri,created.rid}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir},%{_mandir}/man{1,8}} \
	$RPM_BUILD_ROOT{%{ruby_vendorlibdir},%{ruby_vendorarchdir},%{ruby_ridir}} \
	$RPM_BUILD_ROOT%{_bindir} \
	$RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents/apache2 \
	$RPM_BUILD_ROOT%{_datadir}/phusion-passenger/helper-scripts

install -p ext/apache2/mod_passenger.so $RPM_BUILD_ROOT%{_pkglibdir}
install -p ext/ruby/ruby-*/passenger_native_support.so $RPM_BUILD_ROOT%{ruby_vendorarchdir}
install -p bin/passenger-{config,memory-stats,status} bin/passenger $RPM_BUILD_ROOT%{_bindir}
install -p agents/PassengerLoggingAgent agents/PassengerWatchdog $RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents
install -p agents/apache2/PassengerHelperAgent $RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents/apache2
install -p helper-scripts/* $RPM_BUILD_ROOT%{_datadir}/phusion-passenger/helper-scripts
cp -a lib/* $RPM_BUILD_ROOT%{ruby_vendorlibdir}
cp -p man/*.1 $RPM_BUILD_ROOT%{_mandir}/man1
cp -p man/*.8 $RPM_BUILD_ROOT%{_mandir}/man8
cp -a ri/* $RPM_BUILD_ROOT%{ruby_ridir}
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/75_mod_rails.conf

%{__sed} -i -e 's|#!/usr/bin/env ruby|#!%{_bindir}/ruby|' \
	$RPM_BUILD_ROOT%{_bindir}/passenger \
	$RPM_BUILD_ROOT%{_bindir}/passenger-* \
	$RPM_BUILD_ROOT%{_datadir}/phusion-passenger/helper-scripts/*

%{__sed} -i -e 's|#!/usr/bin/env python|#!%{_bindir}/python|' \
	$RPM_BUILD_ROOT%{ruby_vendorlibdir}/phusion_passenger/wsgi/request_handler.py

%clean
rm -rf $RPM_BUILD_ROOT

%post
%service -q httpd restart

%postun
if [ "$1" = "0" ]; then
	%service -q httpd restart
fi

%files
%defattr(644,root,root,755)
%doc INSTALL README
#%doc doc/{A*.txt,Security*.txt,*Apache.txt}
#%doc doc/{A*.html,Security*.html,*Apache.html,images}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/*_mod_rails.conf
%attr(755,root,root) %{_pkglibdir}/mod_passenger.so
%attr(755,root,root) %{_bindir}/passenger
%attr(755,root,root) %{_bindir}/passenger-config
%attr(755,root,root) %{_bindir}/passenger-memory-stats
%attr(755,root,root) %{_bindir}/passenger-status
%{_mandir}/man1/passenger-config.1*
%{_mandir}/man1/passenger-stress-test.1*
%{_mandir}/man8/passenger-memory-stats.8*
%{_mandir}/man8/passenger-status.8*

%attr(755,root,root) %{ruby_vendorarchdir}/passenger_native_support.so
%{ruby_vendorlibdir}/phusion_passenger.rb
%{ruby_vendorlibdir}/phusion_passenger

%dir %{_libdir}/phusion-passenger
%dir %{_libdir}/phusion-passenger/agents
%attr(755,root,root) %{_libdir}/phusion-passenger/agents/PassengerLoggingAgent
%attr(755,root,root) %{_libdir}/phusion-passenger/agents/PassengerWatchdog
%dir %{_libdir}/phusion-passenger/agents/apache2
%attr(755,root,root) %{_libdir}/phusion-passenger/agents/apache2/Passenger*
%dir %{_datadir}/phusion-passenger
%dir %{_datadir}/phusion-passenger/helper-scripts
%attr(755,root,root) %{_datadir}/phusion-passenger/helper-scripts/*

%files ri
%defattr(644,root,root,755)
%{ruby_ridir}/PhusionPassenger

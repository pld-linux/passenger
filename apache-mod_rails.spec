#
# TODO:
# - separate -devel with ExtUtils::Embed and friends?

%define		apxs		/usr/sbin/apxs
%define		mod_name	rails
%define		apacheconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)/conf.d
%define		apachelibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		apacheprefix	%(%{apxs} -q PREFIX 2>/dev/null)
%define		apachelibdir2	%(%{apxs} -q LIBEXECDIR 2>/dev/null | %{__sed} 's|%{apacheprefix}||')

Summary:	A module to bridge Ruby on Rails to Apache
Name:		apache-mod_rails
Version:	3.0.9
Release:	1
License:	Apache
Group:		Networking/Daemons/HTTP
Source0:	http://rubygems.org/downloads/passenger-%{version}.gem
# Source0-md5:	d616c8425071303b983b6c09fea8004a
Source1:	%{name}.conf
Patch0:		%{name}-nogems.patch
Patch1:		%{name}-alias+public.patch
Patch2:		%{name}-build.patch
URL:		http://www.modrails.com
BuildRequires:	apache-base >= 2.0.55-1
BuildRequires:	apache-devel >= 2.0.55-1
BuildRequires:	apache-tools >= 2.0.55-1
BuildRequires:	apr-devel >= 1:1.0.0
BuildRequires:	apr-util-devel >= 1:1.0.0
#BuildRequires:	asciidoc
BuildRequires:	curl-devel
BuildRequires:	libstdc++-devel
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	ruby-devel
BuildRequires:	ruby-rake >= 0.8.0
BuildRequires:	sed >= 4.0
BuildRequires:	zlib-devel
Provides:	apache(mod_rails)
Obsoletes:	apache-mod_rails-rdoc
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

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
%setup -q -c
%{__tar} xf %{SOURCE0} -O data.tar.gz | %{__tar} xz
find -newer README -o -print0 | xargs -0 touch --reference %{SOURCE0}
%patch0 -p1
%patch1 -p0
%patch2 -p1

%{__sed} -i -e 's!/usr/lib/!%{_libdir}/!g' ext/common/ResourceLocator.h

%build
(cd ext/libev ; %{__autoconf})

rake apache2 \
	RELEASE=yes \
	OPTIMIZE=yes \
	APXS2=%{apxs} \
	CXXFLAGS="%{rpmcxxflags}" \
	CFLAGS="%{rpmcflags}" \
	CXX=%{__cxx} \
	CC=%{__cc}

rdoc --ri --op ri lib ext/ruby
%{__rm} -r ri/{ConditionVariable,Exception,GC,IO,Object,Process,Signal}
%{__rm} ri/{cache.ri,created.rid}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{apachelibdir},%{apacheconfdir},%{_mandir}/man{1,8}} \
	$RPM_BUILD_ROOT{%{ruby_rubylibdir},%{ruby_archdir},%{ruby_ridir}} \
	$RPM_BUILD_ROOT%{_bindir} \
	$RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents/apache2 \
	$RPM_BUILD_ROOT%{_datadir}/phusion-passenger/helper-scripts

install ext/apache2/mod_passenger.so $RPM_BUILD_ROOT%{apachelibdir}

install ext/ruby/ruby-*/passenger_native_support.so $RPM_BUILD_ROOT%{ruby_archdir}

install bin/passenger-{config,make-enterprisey,memory-stats,status} bin/passenger \
	$RPM_BUILD_ROOT%{_bindir}

install agents/PassengerLoggingAgent agents/PassengerWatchdog $RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents
install agents/apache2/PassengerHelperAgent $RPM_BUILD_ROOT%{_libdir}/phusion-passenger/agents/apache2

install helper-scripts/* $RPM_BUILD_ROOT%{_datadir}/phusion-passenger/helper-scripts

cp -a lib/* $RPM_BUILD_ROOT%{ruby_rubylibdir}
install man/*.1 $RPM_BUILD_ROOT%{_mandir}/man1
install man/*.8 $RPM_BUILD_ROOT%{_mandir}/man8

cp -a ri/* $RPM_BUILD_ROOT%{ruby_ridir}

install %{SOURCE1} $RPM_BUILD_ROOT%{apacheconfdir}/75_mod_rails.conf

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
%doc INSTALL README doc/{A*.txt,Security*.txt,*Apache.txt}
%doc doc/{A*.html,Security*.html,*Apache.html,images}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{apacheconfdir}/*.conf
%attr(755,root,root) %{apachelibdir}/*
%attr(755,root,root) %{_bindir}/passenger-*
%attr(755,root,root) %{_bindir}/passenger*
%attr(755,root,root) %{ruby_archdir}/*.so
%dir %{_libdir}/phusion-passenger
%dir %{_libdir}/phusion-passenger/agents
%attr(755,root,root) %{_libdir}/phusion-passenger/agents/Passenger*
%dir %{_libdir}/phusion-passenger/agents/apache2
%attr(755,root,root) %{_libdir}/phusion-passenger/agents/apache2/Passenger*
%{ruby_rubylibdir}/phusion_passenger
%{ruby_rubylibdir}/phusion_passenger.rb
%dir %{_datadir}/phusion-passenger
%dir %{_datadir}/phusion-passenger/helper-scripts
%attr(755,root,root) %{_datadir}/phusion-passenger/helper-scripts/*
%{_mandir}/man1/*
%{_mandir}/man8/*

%files ri
%defattr(644,root,root,755)
%{ruby_ridir}/PhusionPassenger

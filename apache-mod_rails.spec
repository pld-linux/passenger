#
# TODO:
# - separate -devel with ExtUtils::Embed and friends?
# - how to pass CXXFLAGS to Rakefile?

%define		apxs		/usr/sbin/apxs
%define		mod_name	rails
%define		apacheconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)/conf.d
%define		apachelibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		apacheprefix	%(%{apxs} -q PREFIX 2>/dev/null)
%define		apachelibdir2	%(%{apxs} -q LIBEXECDIR 2>/dev/null | %{__sed} 's|%{apacheprefix}||')

Summary:	A module to bridge Ruby on Rails to Apache
Name:		apache-mod_rails
Version:	2.2.10
Release:	0.1
License:	Apache
Group:		Networking/Daemons/HTTP
Source0:	http://rubygems.org/downloads/passenger-%{version}.gem
# Source0-md5:	c116ed533ef00eccaffb5a3568cdfd23
Source1:	%{name}.conf
URL:		http://www.modrails.com
BuildRequires:	apache-base >= 2.0.55-1
BuildRequires:	apache-devel >= 2.0.55-1
BuildRequires:	apache-tools >= 2.0.55-1
BuildRequires:	apr-util-devel >= 1:1.0.0
BuildRequires:	pkgconfig
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	ruby-rubygems
BuildRequires:	ruby-devel
BuildRequires:	ruby-rake
BuildRequires:	sed >= 4.0
BuildRequires:	setup.rb
Provides:	apache(mod_rails)
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Phusion Passenger — a.k.a. mod_rails — makes deployment of
applications built on the revolutionary Ruby on Rails web framework a
breeze. It follows the usual Ruby on Rails conventions, such as
“Don’t-Repeat-Yourself”.

%package rdoc
Summary:	HTML documentation for %{pkgname}
Summary(pl.UTF-8):	Dokumentacja w formacie HTML dla %{pkgname}
Group:		Documentation
Requires:	ruby >= 1:1.8.7-4

%description rdoc
HTML documentation for %{pkgname}.

%description rdoc -l pl.UTF-8
Dokumentacja w formacie HTML dla %{pkgname}.

%package ri
Summary:	ri documentation for %{pkgname}
Summary(pl.UTF-8):	Dokumentacja w formacie ri dla %{pkgname}
Group:		Documentation
Requires:	ruby

%description ri
ri documentation for %{pkgname}.

%description ri -l pl.UTF-8
Dokumentacji w formacie ri dla %{pkgname}.

%prep
%setup -q -c
%{__tar} xf %{SOURCE0} -O data.tar.gz | %{__tar} xz
find -newer README -o -print | xargs touch --reference %{SOURCE0}

cp %{_datadir}/setup.rb .

# TODO : ugly metod - but works
%{__sed} -i 's/CXXFLAGS = "/CXXFLAGS = "`pkg-config --cflags apr-util-1`/ ' Rakefile

%{__sed} -i -e 's/rd.template/# rd.template/' Rakefile

%{__sed} -i -e 's|ext/apache2/ApplicationPoolServerExecutable|%{apachelibdir2}/ApplicationPoolServerExecutable|g' ext/common/Utils.cpp

%build
APXS2=%{apxs} rake
APXS2=%{apxs} rake doc

rdoc --ri --op ri lib misc ext
rm -r ri/{ConditionVariable,Exception,GC,IO,Mysql,Object,PlatformInfo,Rake*,Signal}
rm ri/created.rid

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{apachelibdir},%{apacheconfdir},%{_mandir}/man{1,8}} \
	$RPM_BUILD_ROOT{%{ruby_rubylibdir},%{ruby_ridir},%{ruby_rdocdir}} \
	$RPM_BUILD_ROOT{%{ruby_archdir}/phusion_passenger,%{_bindir}}

install ext/apache2/mod_passenger.so $RPM_BUILD_ROOT%{apachelibdir}
install ext/apache2/ApplicationPoolServerExecutable $RPM_BUILD_ROOT%{apachelibdir}

install ext/phusion_passenger/native_support.so $RPM_BUILD_ROOT%{ruby_archdir}/phusion_passenger

install bin/passenger-{config,make-enterprisey,memory-stats,spawn-server,status,stress-test} \
	$RPM_BUILD_ROOT%{_bindir}

cp -a lib/* $RPM_BUILD_ROOT%{ruby_rubylibdir}
install man/*.1 $RPM_BUILD_ROOT%{_mandir}/man1
install man/*.8 $RPM_BUILD_ROOT%{_mandir}/man8

cp -a doc/rdoc $RPM_BUILD_ROOT%{ruby_rdocdir}/%{name}-%{version}
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
%doc INSTALL README doc/*.txt
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{apacheconfdir}/*.conf
%attr(755,root,root) %{apachelibdir}/*
%attr(755,root,root) %{_bindir}/passenger-*
%{ruby_rubylibdir}/phusion_passenger
%dir %{ruby_archdir}/phusion_passenger
%attr(755,root,root) %{ruby_archdir}/phusion_passenger/*.so
%{_mandir}/man1/*
%{_mandir}/man8/*

%files rdoc
%defattr(644,root,root,755)
%{ruby_rdocdir}/%{name}-%{version}

%files ri
%defattr(644,root,root,755)
%{ruby_ridir}/PhusionPassenger

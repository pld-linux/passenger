%define		apxs	/usr/sbin/apxs
%define		mod_name	rails
Summary:	A module to bridge Ruby on Rails to Apache
Name:		apache-mod_rails
Version:	1.0.1
Release:	1
License:	Apache
Group:		Networking/Daemons
Source0:	http://rubyforge.org/frs/download.php/35309/passenger-%{version}.tar.gz
# Source0-md5:	82df07de03c4d57bc2dfc6393bcb7687
#Source1:	%{name}.conf
Patch0:		%{name}-buildfix.patch
URL:		http://www.modrails.com
BuildRequires:	apache-devel >= 2.0.55-1
BuildRequires:	apr-util-devel >= 1:1.0.0
BuildRequires:	rake
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	ruby-devel
BuildRequires:	setup.rb
Provides:	apache(mod_rails)
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

# TODO: separate -devel with ExtUtils::Embed and friends?
%define		apacheconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)/conf.d
%define		apachelibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)

%description
Phusion Passenger — a.k.a. mod_rails — makes deployment of
applications built on the revolutionary Ruby on Rails web framework a
breeze. It follows the usual Ruby on Rails conventions, such as
“Don’t-Repeat-Yourself”.

%prep
%setup -q -n passenger-%{version}
%patch0 -p1

%build
cp %{_datadir}/setup.rb .
APXS2=%{apxs} rake
ruby setup.rb config --rbdir=%{ruby_rubylibdir} --sodir=%{ruby_archdir}
ruby setup.rb setup

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{apachelibdir},%{apacheconfdir}}

install ext/apache2/mod_passenger.so $RPM_BUILD_ROOT%{apachelibdir}
ruby setup.rb install --prefix=$RPM_BUILD_ROOT

#install %{SOURCE1} $RPM_BUILD_ROOT%{apacheconfdir}/75_mod_rails.conf

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
#%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{apacheconfdir}/*.conf
%attr(755,root,root) %{apachelibdir}/*.so
%attr(755,root,root) %{_bindir}/passenger-spawn-server
%{ruby_rubylibdir}/passenger

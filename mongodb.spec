%global daemon mongod

Name:           mongodb
Version:        2.4.9
Release:        3%{?dist}
Summary:        High-performance, schema-free document-oriented database
Group:          Applications/Databases
License:        AGPLv3 and zlib and ASL 2.0
# util/md5 is under the zlib license
# manpages and bson are under ASL 2.0
# everything else is AGPLv3
URL:            http://www.mongodb.org

Source0:        http://fastdl.mongodb.org/src/%{name}-src-r%{version}.tar.gz
Source1:        %{name}.init
Source2:        %{name}.logrotate
Source3:        %{name}.conf
Source4:        %{daemon}.sysconf
Source5:        %{name}-tmpfile
Source6:        %{daemon}.service
Patch1:         mongodb-2.4.5-no-term.patch
##Patch 2 - make it possible to use system libraries
Patch2:         mongodb-2.4.5-use-system-version.patch
##Patch 5 - https://jira.mongodb.org/browse/SERVER-9210
Patch5:         mongodb-2.4.5-boost-fix.patch
##Patch 6 - https://github.com/mongodb/mongo/commit/1d42a534e0eb1e9ac868c0234495c0333d57d7c1
Patch6:         mongodb-2.4.5-boost-size-fix.patch
##Patch 7 - https://bugzilla.redhat.com/show_bug.cgi?id=958014
## Need to work on getting this properly patched upstream
Patch7:         mongodb-2.4.5-pass-flags.patch
##Patch 8 - Compile with GCC 4.8
Patch8:         mongodb-2.4.5-gcc48.patch
##Patch 10 - Support atomics on ARM
Patch10:        mongodb-2.4.5-atomics.patch
# fix arm build (fixed in upstream from 2.5.x)
Patch11:        mongodb-2.4.5-signed-char-for-BSONType-enumerations.patch

Requires:       v8 >= 3.14.5.10
BuildRequires:  boost-devel
BuildRequires:  libpcap-devel
BuildRequires:  openssl-devel
BuildRequires:  pcre-devel
BuildRequires:  python-devel
BuildRequires:  readline-devel
BuildRequires:  scons
BuildRequires:  snappy-devel
BuildRequires:  v8-devel
%if 0%{?fedora} || 0%{?rhel} >= 7
BuildRequires:  systemd
%endif
%ifnarch aarch64
BuildRequires:  gperftools-devel
%endif

# Mongodb must run on a little-endian CPU (see bug #630898)
ExcludeArch:    ppc ppc64 %{sparc} s390 s390x

%description
Mongo (from "humongous") is a high-performance, open source, schema-free
document-oriented database. MongoDB is written in C++ and offers the following
features:
    * Collection oriented storage: easy storage of object/JSON-style data
    * Dynamic queries
    * Full index support, including on inner objects and embedded arrays
    * Query profiling
    * Replication and fail-over support
    * Efficient storage of binary data including large objects (e.g. photos
    and videos)
    * Auto-sharding for cloud-level scalability (currently in early alpha)
    * Commercial Support Available

A key goal of MongoDB is to bridge the gap between key/value stores (which are
fast and highly scalable) and traditional RDBMS systems (which are deep in
functionality).

%package -n lib%{name}
Summary:        MongoDB shared libraries
Group:          Development/Libraries

%description -n lib%{name}
This package provides the shared library for the MongoDB client.

%package -n lib%{name}-devel
Summary:        MongoDB header files
Group:          Development/Libraries
Requires:       lib%{name}%{?_isa} = %{version}-%{release}
Requires:       boost-devel
Provides:       mongodb-devel = %{version}-%{release}
Obsoletes:      mongodb-devel < 2.4

%description -n lib%{name}-devel
This package provides the header files and C++ driver for MongoDB. MongoDB is
a high-performance, open source, schema-free document-oriented database.

%package server
Summary:        MongoDB server, sharding server and support scripts
Group:          Applications/Databases
Requires:       v8
Requires(pre):  shadow-utils
%if 0%{?fedora} || 0%{?rhel} >= 7
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
%else
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(postun): initscripts
%endif

%description server
This package provides the mongo server software, mongo sharding server
software, default configuration files, and init scripts.


%prep
%setup -q -n mongodb-src-r%{version}
%patch1 -p1
%patch2 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch10 -p1 -b .atomics
%patch11 -p1 -b .type

# spurious permissions
chmod -x README

# wrong end-of-file encoding
sed -i 's/\r//' README

# Put lib dir in correct place
# https://jira.mongodb.org/browse/SERVER-10049
sed -i -e "s@\$INSTALL_DIR/lib@\$INSTALL_DIR/%{_lib}@g" src/SConscript.client

%build
# NOTE: Build flags must be EXACTLY the same in the install step!
# If you fail to do this, mongodb will be built twice...
scons \
        %{?_smp_mflags} \
        --sharedclient \
        --use-system-all \
        --prefix=%{buildroot}%{_prefix} \
        --extrapath=%{_prefix} \
        --usev8 \
        --nostrip \
        --ssl \
        --full

%install
# NOTE: Install flags must be EXACTLY the same in the build step!
# If you fail to do this, mongodb will be built twice...
scons install \
        %{?_smp_mflags} \
        --sharedclient \
        --use-system-all \
        --prefix=%{buildroot}%{_prefix} \
        --extrapath=%{_prefix} \
        --usev8 \
        --nostrip \
        --ssl \
        --full

find %{buildroot} -name '*.a' -exec rm -f {} ';'

mkdir -p %{buildroot}%{_sharedstatedir}/%{name}
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig

%if 0%{?fedora} || 0%{?rhel} >= 7
mkdir -p %{buildroot}%{_unitdir}
install -p -D -m 644 %{SOURCE5} %{buildroot}%{_libdir}/../lib/tmpfiles.d/mongodb.conf
install -p -D -m 644 %{SOURCE6} %{buildroot}%{_unitdir}/%{daemon}.service
%else
install -p -D -m 755 %{SOURCE1} %{buildroot}%{_initddir}/%{daemon}
%endif
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/mongodb.conf
install -p -D -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/sysconfig/%{daemon}

mkdir -p %{buildroot}%{_mandir}/man1
cp -p debian/*.1 %{buildroot}%{_mandir}/man1/

%post -n lib%{name}
/sbin/ldconfig

%postun -n lib%{name}
/sbin/ldconfig

%pre server
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
useradd -r -g %{name} -u 184 -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
-c "MongoDB Database Server" %{name}
exit 0

%post server
%if 0%{?fedora} || 0%{?rhel} >= 7
# https://fedoraproject.org/wiki/Packaging:ScriptletSnippets#Systemd
%tmpfiles_create %{?scl_prefix}mongodb.conf
# daemon-reload
%systemd_postun
%else
/sbin/chkconfig --add %{daemon}
%endif

%preun server
if [ $1 = 0 ] ; then
%if 0%{?fedora} || 0%{?rhel} >= 7
  # --no-reload disable; stop
  %systemd_preun %{daemon}.service
%else
  /sbin/service %{daemon} stop &>/dev/null
  /sbin/chkconfig --del %{daemon}
%endif
fi


%postun server
%if 0%{?fedora} || 0%{?rhel} >= 7
# daemon-reload
%systemd_postun
%endif
if [ "$1" -ge "1" ] ; then
%if 0%{?fedora} || 0%{?rhel} >= 7
  # try-restart
  %systemd_postun_with_restart %{daemon}.service
%else
  /sbin/service %{daemon} condrestart &>/dev/null || :
%endif
fi


%files
%{_bindir}/bsondump
%{_bindir}/mongo
%{_bindir}/mongodump
%{_bindir}/mongoexport
%{_bindir}/mongofiles
%{_bindir}/mongoimport
%{_bindir}/mongooplog
%{_bindir}/mongoperf
%{_bindir}/mongorestore
%{_bindir}/mongosniff
%{_bindir}/mongostat
%{_bindir}/mongotop

%{_mandir}/man1/bsondump.1*
%{_mandir}/man1/mongo.1*
%{_mandir}/man1/mongodump.1*
%{_mandir}/man1/mongoexport.1*
%{_mandir}/man1/mongofiles.1*
%{_mandir}/man1/mongoimport.1*
%{_mandir}/man1/mongooplog.1*
%{_mandir}/man1/mongoperf.1*
%{_mandir}/man1/mongorestore.1*
%{_mandir}/man1/mongosniff.1*
%{_mandir}/man1/mongostat.1*
%{_mandir}/man1/mongotop.1*

%files -n lib%{name}
%doc README GNU-AGPL-3.0.txt APACHE-2.0.txt
%{_libdir}/libmongoclient.so

# usually contains ln -s /usr/lib/<???> lib<???>.so
%files -n lib%{name}-devel
%{_includedir}/*

%files server
%{_bindir}/mongod
%{_bindir}/mongos
%{_mandir}/man1/mongod.1*
%{_mandir}/man1/mongos.1*
%dir %attr(0750, %{name}, root) %{_sharedstatedir}/%{name}
%dir %attr(0750, %{name}, root) %{_localstatedir}/log/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/mongodb.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{daemon}
%if 0%{?fedora} || 0%{?rhel} >= 7
%{_unitdir}/*.service
%{_libdir}/../lib/tmpfiles.d/mongodb.conf
%else
%dir %attr(0750, %{name}, root) %{_localstatedir}/run/%{name}
%{_initddir}/%{daemon}
%endif

%changelog
* Fri Feb 14 2014 T.C. Hollingsworth <tchollingsworth@gmail.com> - 2.4.9-3
- rebuild for icu-53 (via v8)

* Tue Feb 04 2014 Matthias Saou <matthias@saou.eu> 2.4.9-2
- Merge el6 branch changes (we shouldn't start diverging now).
- Re-introduce conditionals, but to still support EL6.
- Include run directory only for EL6.
- Don't own the /usr/include directory.
- Make libmongodb requirement arch specific (#1010535).
- Fix multiple_occurrences error from duplicate --quiet options (#1022476).
- Fix broken v8 version specific requirement (#1027157).

* Sun Jan 19 2014 Peter Robinson <pbrobinson@fedoraproject.org> 2.4.9-1
- Update to 2.4.9
- Drop old < F-15 conditionals
- Cleanup Spec
- Run ldconfig for the lib package, not binary package
- Don't make some directories world readable (RHBZ 857926)

* Mon Jan 06 2014 Jan Pacner <jpacner@redhat.com> - 2.4.6-3
- Resolves: #1027157 (mongo shell sefgaults when using arbitrary v8 version)

* Thu Nov 28 2013 Jan Pacner <jpacner@redhat.com> - 2.4.8-1
- new release
- Resolves: #1010712 (LimitNOFILE)
- make sysconf options being respected

* Wed Aug 21 2013 Troy Dawson <tdawson@redhat.com> - 2.4.6-1
- Updated to 2.4.6
- Added Requires: v8  (#971595)

* Sun Jul 28 2013 Petr Machata <pmachata@redhat.com> - 2.4.5-6
- Rebuild for boost 1.54.0

* Sat Jul 27 2013 pmachata@redhat.com - 2.4.5-5
- Rebuild for boost 1.54.0

* Fri Jul 12 2013 Troy Dawson <tdawson@redhat.com> - 2.4.5-4
- Added Provides: mongodb-devel to libmongodb-devel

* Fri Jul 12 2013 Troy Dawson <tdawson@redhat.com> - 2.4.5-3
- Removed hardening section.  Currently doesn't work with 2.4.x
  Wasn't really being applied when we thought it was.
- Cleaned up RHEL5 spec leftovers

* Thu Jul 11 2013 David Marlin <dmarlin@redhat.com> - 2.4.5-2
- Updated arm patches to work with 2.4.x

* Mon Jul 08 2013 Troy Dawson <tdawson@redhat.com> - 2.4.5-1
- Update to version 2.4.5 to fix CVE-2013-4650
- Patch3 fixed upstream - https://jira.mongodb.org/browse/SERVER-5575
- Patch4 fixed upstream - https://jira.mongodb.org/browse/SERVER-6514
- Put lib dir in correct place
- no longer have to remove duplicate headers

* Sun Jul 07 2013 Johan Hedin <johan.o.hedin@gmail.com> - 2.4.4-4
- Added patch to make mongodb compile with gcc 4.8

* Wed Jul 03 2013 Johan Hedin <johan.o.hedin@gmail.com> - 2.4.4-3
- Added missing daemon name to the preun script for the server
- Fixed init script so that it does not kill the server on shutdown
- Renamed mongodb-devel to libmongdb-devel
- Dependency cleanup between the sub packages
- Moved Requires for the server to the server sub package
- Using %%{_unitdir} macro for where to put systemd unit files
- Fixed rpmlint warnings regarding %% in comments and mixed tabs/spaces
- Run systemd-tmpfiles --create mongodb.conf in post server

* Mon Jul 01 2013 Troy Dawson <tdawson@redhat.com> - 2.4.4-2
- Turn on hardened build (#958014)
- Apply patch to accept env flags

* Sun Jun 30 2013 Johan Hedin <johan.o.hedin@gmail.com> - 2.4.4-1
- Bumped version up to 2.4.4
- Rebased the old 2.2 patches that are still needed to 2.4.4
- Added some new patches to build 2.4.4 properly

* Sat May 04 2013 David Marlin <dmarlin@redhat.com> - 2.2.4-2
- Updated patch to work on both ARMv5 and ARMv7 (#921226)

* Thu May 02 2013 Troy Dawson <tdawson@redhat.com> - 2.2.4-1
- Bumped version up to 2.2.4
- Refreshed all patches to 2.2.4

* Fri Apr 26 2013 David Marlin <dmarlin@redhat.com> - 2.2.3-5
- Patch to build on ARM (#921226)

* Wed Mar 27 2013 Troy Dawson <tdawson@redhat.com> - 2.2.3-4
- Fix for CVE-2013-1892

* Sun Feb 10 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 2.2.3-3
- Rebuild for Boost-1.53.0

* Sat Feb 09 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 2.2.3-2
- Rebuild for Boost-1.53.0

* Tue Feb 05 2013 Troy Dawson <tdawson@redhat.com> - 2.2.3-1
- Update to version 2.2.3

* Mon Jan 07 2013 Troy Dawson <tdawson@redhat.com> - 2.2.2-2
- remove duplicate headers (#886064)

* Wed Dec 05 2012 Troy Dawson <tdawson@redhat.com> - 2.2.2-1
- Updated to version 2.2.2

* Tue Nov 27 2012 Troy Dawson <tdawson@redhat.com> - 2.2.1-3
- Add ssl build option
- Using the reserved mongod UID for the useradd
- mongod man page in server package (#880351)
- added optional MONGODB_OPTIONS to init script

* Wed Oct 31 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.2.1-2
- Make sure build and install flags are the same
- Actually remove the js patch file

* Wed Oct 31 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.2.1-1
- Remove fork fix patch (fixed upstream)
- Remove pcre patch (fixed upstream)
- Remove mozjs patch (now using v8 upstream)
- Update to 2.2.1

* Tue Oct 02 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-6
- full flag patch to get 32 bit builds to work

* Tue Oct 02 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-5
- shared libraries patch
- Fix up minor %%files issues

* Fri Sep 28 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-4
- Fix spec files problems

* Fri Sep 28 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-3
- Updated patch to use system libraries
- Update init script to use a pidfile

* Thu Sep 27 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-2
- Added patch to use system libraries

* Wed Sep 19 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-1
- Updated to 2.2.0
- Updated patches that were still needed
- use v8 instead of spider_monkey due to bundled library issues

* Tue Aug 21 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.7-1
- Update to 2.0.7
- Don't patch for boost-filesystem version 3 on EL6

* Mon Aug 13 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-3
- Remove EL5 support
- Add patch to use boost-filesystem version 3

* Wed Aug 01 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-2
- Don't apply fix-xtime patch on EL5

* Wed Aug 01 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-1
- Update to 2.0.6
- Update no-term patch
- Add fix-xtime patch for new boost

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Apr 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.4-1
- Update to 2.0.4
- Remove oldpython patch (fixed upstream)
- Remove snappy patch (fixed upstream)

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.2-10
- Rebuilt for c++ ABI breakage

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 2.0.2-9
- Rebuild against PCRE 8.30

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-8
- Disable HTTP interface by default (#752331)

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-7
- Enable journaling by default (#656112)
- Remove BuildRequires on unittest (#755081)

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-6
- Clean up mongodb-src-r2.0.2-js.patch and fix #787246

* Tue Jan 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-5
- Enable build using external snappy

* Tue Jan 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-4
- Patch buildsystem for building on older pythons (RHEL5)

* Mon Jan 16 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-3
- Merge the 2.0.2 spec file with EPEL
- Merge mongodb-sm-pkgconfig.patch into mongodb-src-r2.0.2-js.patch

* Mon Jan 16 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-2
- Add pkg-config enablement patch

* Sat Jan 14 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-1
- Update to 2.0.2
- Add new files (mongotop and bsondump manpage)
- Update mongodb-src-r1.8.2-js.patch => mongodb-src-r2.0.2-js.patch
- Update mongodb-fix-fork.patch
- Fix pcre linking

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.2-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Nov 20 2011 Chris Lalancette <clalancette@gmail.com> - 1.8.2-10
- Rebuild for rawhide boost update

* Thu Sep 22 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-9
- Copy the right source file into place for tmpfiles.d

* Tue Sep 20 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-8
- Add a tmpfiles.d file to create the /var/run/mongodb subdirectory

* Mon Sep 12 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-7
- Add a patch to fix the forking to play nice with systemd
- Make the /var/run/mongodb directory owned by mongodb

* Thu Jul 28 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-6
- BZ 725601 - fix the javascript engine to not hang (thanks to Eduardo Habkost)

* Mon Jul 25 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-5
- Fixes to post server, preun server, and postun server to use systemd

* Thu Jul 21 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-4
- Update to use systemd init

* Thu Jul 21 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-3
- Rebuild for boost ABI break

* Wed Jul 13 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-2
- Make mongodb-devel require boost-devel (BZ 703184)

* Fri Jul 01 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-1
- Update to upstream 1.8.2
- Add patch to ignore TERM

* Fri Jul 01 2011 Chris Lalancette <clalance@redhat.com> - 1.8.0-3
- Bump release to build against new boost package

* Sat Mar 19 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.8.0-2
- Make mongod bind only to 127.0.0.1 by default

* Sat Mar 19 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.8.0-1
- Update to 1.8.0
- Remove upstreamed nonce patch

* Wed Feb 16 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-5
- Add nonce patch

* Sun Feb 13 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-4
- Manually define to use boost-fs v2

* Sat Feb 12 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-3
- Disable extra warnings

* Fri Feb 11 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-2
- Disable compilation errors on warnings

* Fri Feb 11 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-1
- Update to 1.7.5
- Remove CPPFLAGS override
- Added libmongodb package

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Dec 06 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-3
- Add post/postun ldconfig... oops!

* Mon Dec 06 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-2
- Enable --sharedclient option, remove static lib

* Sat Dec 04 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-1
- New upstream release

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-4
- Put -fPIC onto both the build and install scons calls

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-3
- Define _initddir when it doesn't exist for el5 and others

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-2
- Added -fPIC build option which was dropped by accident

* Thu Oct  7 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.3-1
- removed js Requires
- new upstream release
- added more excludearches: sparc s390, s390x and bugzilla pointer

* Tue Sep  7 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.2-2
- added ExcludeArch for ppc

* Fri Sep  3 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.2-1
- new upstream release 1.6.2
- send mongod the USR1 signal when doing logrotate
- use config options when starting the daemon from the initfile
- removed dbpath patch: rely on config
- added pid directory to config file and created the dir in the spec
- made the init script use options from the config file
- changed logpath in mongodb.conf

* Wed Sep  1 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.1-1
- new upstream release 1.6.1
- patched SConstruct to allow setting cppflags
- stopped using sed and chmod macros

* Fri Aug  6 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.0-1
- new upstream release: 1.6.0
- added -server package
- added new license file to %%docs
- fix spurious permissions and EOF encodings on some files

* Tue Jun 15 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.4.3-2
- added explicit js requirement
- changed some names

* Wed May 26 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.4.3-1
- updated to 1.4.3
- added zlib license for util/md5
- deleted upstream deb/rpm recipes
- made scons not strip binaries
- made naming more consistent in logfile, lockfiles, init scripts etc.
- included manpages and added corresponding license
- added mongodb.conf to sources

* Fri Oct  2 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-3
- fixed libpath issue for 64bit systems

* Thu Oct  1 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-2
- added virtual -static package

* Mon Aug 31 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-1
- Initial release.

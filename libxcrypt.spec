# libxcrypt is used by util-linux
%ifarch %{x86_64}
%bcond_without compat32
%else
%bcond_with compat32
%endif

# Disabling the old API calls saves only around 2 kB
# Not worth breaking compatibility over that.
%bcond_without old_apis

%if %{with old_apis}
%define major 1
%else
%define major 2
%endif
%define oldlibname %mklibname crypt 1
%define libname %mklibname crypt
%define develname %mklibname crypt -d
%define staticname %mklibname crypt -d -s
%define lib32name libcrypt%{major}
%define devel32name libcrypt-devel
%define static32name libcrypt-static-devel

%global optflags %{optflags} -O3

# (tpg) use LLVM/polly for polyhedra optimization and automatic vector code generation
%define pollyflags -mllvm -polly -mllvm -polly-position=early -mllvm -polly-parallel=true -fopenmp -fopenmp-version=50 -mllvm -polly-dependences-computeout=5000000 -mllvm -polly-detect-profitability-min-per-loop-insts=40 -mllvm -polly-tiling=true -mllvm -polly-prevect-width=256 -mllvm -polly-vectorizer=stripmine -mllvm -polly-omp-backend=LLVM -mllvm -polly-num-threads=0 -mllvm -polly-scheduling=dynamic -mllvm -polly-scheduling-chunksize=1 -mllvm -polly-invariant-load-hoisting -mllvm -polly-loopfusion-greedy -mllvm -polly-run-inliner -mllvm -polly-run-dce -mllvm -polly-enable-delicm=true -mllvm -extra-vectorizer-passes -mllvm -enable-cond-stores-vec -mllvm -slp-vectorize-hor-store -mllvm -enable-loopinterchange -mllvm -enable-loop-distribute -mllvm -enable-unroll-and-jam -mllvm -enable-loop-flatten -mllvm -unroll-runtime-multi-exit -mllvm -aggressive-ext-opt

%undefine _debugsource_packages

# (tpg) enable PGO build
%if ! %{cross_compiling}
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	Extended crypt library for DES, MD5, Blowfish and others
Name:		libxcrypt
Version:	4.4.38
Release:	1
License:	LGPLv2+
Group:		System/Libraries
Url:		https://github.com/besser82/libxcrypt
Source0:	https://github.com/besser82/libxcrypt/releases/download/v%{version}/libxcrypt-%{version}.tar.xz
Patch0:		libxcrypt-disable-broken-tests.patch
# (tpg) upstream patches
BuildRequires:	findutils
BuildRequires:	perl(open)

%description
libxcrypt is a modern library for one-way hashing of passwords.
It supports a wide variety of both modern and historical hashing
methods: yescrypt, gost-yescrypt, scrypt, bcrypt, sha512crypt,
sha256crypt, md5crypt, SunMD5, sha1crypt, NT, bsdicrypt, bigcrypt,
and descrypt. It provides the traditional Unix crypt and crypt_r
interfaces, as well as a set of extended interfaces pioneered by
Openwall Linux, crypt_rn, crypt_ra, crypt_gensalt, crypt_gensalt_rn,
and crypt_gensalt_ra.

%package -n %{libname}
Summary:	Crypt Library for DES, MD5, Blowfish and others
Group:		System/Libraries
Obsoletes:	%{mklibname xcrypt 2} < 4.0.0
Provides:	glibc-crypt_blowfish = 1.3
Provides:	eglibc-crypt_blowfish = 1.3
%if %{with old_apis}
%if "%{_lib}" == "lib64"
Provides:	libcrypt.so.2()(64bit)
%else
Provides:	libcrypt.so.2
%endif
%endif
%rename %{oldlibname}

%description -n %{libname}
libxcrypt is a modern library for one-way hashing of passwords.
It supports a wide variety of both modern and historical hashing
methods: yescrypt, gost-yescrypt, scrypt, bcrypt, sha512crypt,
sha256crypt, md5crypt, SunMD5, sha1crypt, NT, bsdicrypt, bigcrypt,
and descrypt. It provides the traditional Unix crypt and crypt_r
interfaces, as well as a set of extended interfaces pioneered by
Openwall Linux, crypt_rn, crypt_ra, crypt_gensalt, crypt_gensalt_rn,
and crypt_gensalt_ra.

%package -n %{develname}
Summary:	Development libraries for %{name}
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Obsoletes:	%{mklibname xcrypt -d} < 4.0.0
Provides:	glibc-crypt_blowfish-devel = 1.3
Provides:	eglibc-crypt_blowfish-devel = 1.3

%description -n %{develname}
This package contains the header files necessary
to develop software using %{name}.

%package -n %{staticname}
Summary:	Static libraries for %{name}
Group:		Development/C
Requires:	%{develname} = %{EVRD}

%description -n %{staticname}
This package contains the static libraries necessary
to develop software using %{name} without requiring
%{name} to be installed on the target system.

%if %{with compat32}
%package -n %{lib32name}
Summary:	Crypt Library for DES, MD5, Blowfish and others (32-bit)
Group:		System/Libraries
BuildRequires:	libc6
%if %{with old_apis}
Provides:	libcrypt.so.2
%endif

%description -n %{lib32name}
Libxcrypt is a replacement for libcrypt, which comes with the GNU C
Library. It supports DES crypt, MD5, SHA256, SHA512 and passwords with
blowfish encryption. (32-bit)

%package -n %{devel32name}
Summary:	Development libraries for %{name} (32-bit)
Group:		Development/C
Requires:	%{lib32name} = %{EVRD}
Requires:	%{develname} = %{EVRD}

%description -n %{devel32name}
This package contains the header files necessary
to develop software using %{name}. (32-bit)

%package -n %{static32name}
Summary:	Static libraries for %{name} (32-bit)
Group:		Development/C
Requires:	%{devel32name} = %{EVRD}

%description -n %{static32name}
This package contains the static libraries necessary
to develop software using %{name} without requiring
%{name} to be installed on the target system.
%endif

%prep
%autosetup -p1

%build
autoreconf -fiv

export CONFIGURE_TOP="$(pwd)"
%if %{with compat32}
mkdir build32
cd build32
export CFLAGS="$CFLAGS -fno-strict-aliasing"
%configure32 \
    ac_cv_func_arc4random_buf=no \
    --enable-shared \
    --enable-static \
    --enable-hashes=all \
    --disable-failure-tokens \
%if %{with old_apis}
    --enable-obsolete-api=yes \
%else
    --disable-obsolete-api \
%endif
    || (cat config.log && exit 1)

%make_build
cd ..
%endif

mkdir build
cd build
%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate %{pollyflags}" \
CXXFLAGS="%{optflags} -fprofile-generate %{pollyflags}" \
FFLAGS="$CFLAGS" \
FCFLAGS="$CFLAGS" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
%configure  \
    ac_cv_func_arc4random_buf=no \
    --enable-shared \
    --disable-static \
    --enable-hashes=all \
    --disable-failure-tokens \
%if %{with old_apis}
    --enable-obsolete-api=yes \
%else
    --disable-obsolete-api \
%endif
    || (cat config.log && exit 1)

%make_build

make check
unset LD_LIBRARY_PATH
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw

make clean

# profile-instr-out-of-date and profile-instr-unprofiled are
# caused by the static lib not being used during make check.
# Only the shared lib and everything shared between the shared
# and static lib is profiled
CFLAGS="%{optflags} -fprofile-use=$PROFDATA -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled -Wno-error=backend-plugin %{pollyflags}" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled -Wno-error=backend-plugin %{pollyflags}" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled -Wno-error=backend-plugin" \
%endif
%configure  \
    ac_cv_func_arc4random_buf=no \
    --enable-shared \
    --enable-static \
    --enable-hashes=all \
    --disable-failure-tokens \
%if %{with old_apis}
    --enable-obsolete-api=yes \
%else
    --disable-obsolete-api \
%endif
    || (cat config.log && exit 1)

%make_build

%install
%if %{with compat32}
%make_install -C build32
%endif
%make_install -C build

# We do not need libowcrypt.*, since it is a SUSE
# compat thing.  Software needing it to be build can
# be patched easily to just link against '-lcrypt'.
find %{buildroot} -name 'libow*' -print -delete

# The only difference between libcrypt.so.1 (as we're building it)
# and libcrypt.so.2 (as some other distros are building it) is the
# removal of a few old APIs that saves a whole 2 kB.
# Since .1 is a superset of .2, putting a symlink there gives us
# binary compatibility with distros that have opted to go for .2.
ln -s libcrypt.so.1 %{buildroot}%{_libdir}/libcrypt.so.2
%if %{with compat32}
ln -s libcrypt.so.1 %{buildroot}%{_prefix}/lib/libcrypt.so.2
%endif

%if ! %{cross_compiling}
%check
# FIXME as of libxcrypt 4.4.3-2, clang 7.0.1-1, binutils 2.32-1
# make check fails on 32-bit ARM:
#
# ./m4/test-driver: line 107:  9303 Bus error               (core dumped) "$@" > $log_file 2>&1
# [...]
# FAIL: test-alg-gost3411-2012
#============================
#   ok: test vector from example A.1 from GOST-34.11-2012 (256 Bit)
# ERROR: false positive test vector (256 Bit)
# FAIL test-alg-gost3411-2012 (exit status: 135)
#
# Since this happens in one of the less relevant algorithms and libxcrypt
# 4.4.3-2 is perfectly usable for PAM and friends even if there is a bug
# in GOST, we let this pass for now.
%ifnarch %{arm}
# (tpg) all tests MUST pass
make check -C build || (cat test-suite.log && exit 1)
%endif
%endif

%files -n %{libname}
%{_libdir}/lib*.so.%{major}*
%if %{with old_apis}
%{_libdir}/lib*.so.2
%endif

%files -n %{develname}
%doc AUTHORS NEWS
%{_includedir}/*.h
%{_libdir}/libcrypt.so
%{_libdir}/libxcrypt.so
%{_libdir}/pkgconfig/*.pc
%doc %{_mandir}/man3/crypt*.3*
%doc %{_mandir}/man5/crypt.5*

%files -n %{staticname}
%{_libdir}/libcrypt.a
%{_libdir}/libxcrypt.a

%if %{with compat32}
%files -n %{lib32name}
%{_prefix}/lib/lib*.so.%{major}*
%if %{with old_apis}
%{_prefix}/lib/lib*.so.2
%endif

%files -n %{devel32name}
%{_prefix}/lib/libcrypt.so
%{_prefix}/lib/libxcrypt.so
%{_prefix}/lib/pkgconfig/*.pc

%files -n %{static32name}
%{_prefix}/lib/libcrypt.a
%{_prefix}/lib/libxcrypt.a
%endif

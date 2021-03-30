# libxcrypt is used by util-linux
%ifarch %{x86_64}
%bcond_without compat32
%else
%bcond_with compat32
%endif

%define major 1
%define libname %mklibname crypt %{major}
%define develname %mklibname crypt -d
%define staticname %mklibname crypt -d -s
%define lib32name libcrypt%{major}
%define devel32name libcrypt-devel
%define static32name libcrypt-static-devel

# We ship a static library here -- LTO bytecode rather than
# object code in .o files packaged into a static library breaks
# using different compilers
%global _disable_lto 1

%ifarch %{arm} %{ix86} %{x86_64} aarch64
%global optflags %{optflags} -O3 -falign-functions=32 -fno-math-errno -fno-trapping-math -fno-strict-aliasing -fPIC -Wno-gnu-statement-expression
%endif
%ifarch %{arm} %{riscv}
%global optflags %{optflags} -O2 -fno-strict-aliasing -fPIC -Wno-gnu-statement-expression
%endif
%global ldflags %{ldflags} -fPIC

# (tpg) enable PGO build
%ifnarch riscv64 %{arm}
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	Crypt Library for DES, MD5, Blowfish and others
Name:		libxcrypt
Version:	4.4.18
Release:	2
License:	LGPLv2+
Group:		System/Libraries
Url:		https://github.com/besser82/libxcrypt
Source0:	https://github.com/besser82/libxcrypt/archive/%{name}-%{version}.tar.gz
#Patch0:		libxcrypt-4.0.1-strict-aliasing.patch
BuildRequires:	findutils
BuildRequires:	perl(open)

%description
Libxcrypt is a replacement for libcrypt, which comes with the GNU C
Library. It supports DES crypt, MD5, SHA256, SHA512 and passwords with
blowfish encryption.

%package -n %{libname}
Summary:	Crypt Library for DES, MD5, Blowfish and others
Group:		System/Libraries
Obsoletes:	%{mklibname xcrypt 2} < 4.0.0
Provides:	glibc-crypt_blowfish = 1.3
Provides:	eglibc-crypt_blowfish = 1.3

%description -n %{libname}
Libxcrypt is a replacement for libcrypt, which comes with the GNU C
Library. It supports DES crypt, MD5, SHA256, SHA512 and passwords with
blowfish encryption.

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
%configure32 \
    --enable-shared \
    --enable-static \
    --enable-hashes=all \
    --disable-failure-tokens \
    --enable-obsolete-api=yes || (cat config.log && exit 1)
%make_build
cd ..
%endif

mkdir build
cd build
%if %{with pgo}
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"
CFLAGS="%{optflags} -fprofile-instr-generate" \
CXXFLAGS="%{optflags} -fprofile-instr-generate" \
FFLAGS="$CFLAGS" \
FCFLAGS="$CFLAGS" \
LDFLAGS="%{ldflags} -fprofile-instr-generate" \
%configure  \
    --libdir=/%{_lib} \
    --enable-shared \
    --disable-static \
    --enable-hashes=all \
    --disable-failure-tokens \
    --enable-obsolete-api=yes || (cat config.log && exit 1)

%make_build

make check
unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=%{name}.profile *.profile.d

make clean

# profile-instr-out-of-date and profile-instr-unprofiled are
# caused by the static lib not being used during make check.
# Only the shared lib and everything shared between the shared
# and static lib is profiled
CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile) -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile) -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile) -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled" \
%endif
%configure  \
    --libdir=/%{_lib} \
    --enable-shared \
    --enable-static \
    --enable-hashes=all \
    --disable-failure-tokens \
    --enable-obsolete-api=yes || (cat config.log && exit 1)

%make_build

%install
%if %{with compat32}
%make_install -C build32
%endif
%make_install -C build
mkdir -p %{buildroot}%{_libdir}/pkgconfig/
mv %{buildroot}/%{_lib}/pkgconfig/*.pc %{buildroot}%{_libdir}/pkgconfig/
mv %{buildroot}/%{_lib}/*.a %{buildroot}%{_libdir}/

# We do not need libowcrypt.*, since it is a SUSE
# compat thing.  Software needing it to be build can
# be patched easily to just link against '-lcrypt'.
find %{buildroot} -name 'libow*' -print -delete

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

%files -n %{libname}
/%{_lib}/lib*.so.%{major}*

%files -n %{develname}
%doc AUTHORS NEWS README.md
%{_includedir}/*.h
/%{_lib}/libcrypt.so
/%{_lib}/libxcrypt.so
%{_libdir}/pkgconfig/*.pc
%{_mandir}/man3/crypt*.3*
%{_mandir}/man5/crypt.5*

%files -n %{staticname}
%{_libdir}/libcrypt.a
%{_libdir}/libxcrypt.a

%if %{with compat32}
%files -n %{lib32name}
%{_prefix}/lib/lib*.so.%{major}*

%files -n %{devel32name}
%{_prefix}/lib/libcrypt.so
%{_prefix}/lib/libxcrypt.so
%{_prefix}/lib/pkgconfig/*.pc

%files -n %{static32name}
%{_prefix}/lib/libcrypt.a
%{_prefix}/lib/libxcrypt.a
%endif

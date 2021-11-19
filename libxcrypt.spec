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

%ifarch %{arm} %{ix86} %{x86_64} aarch64
%global optflags %{optflags} -O3 -falign-functions=32 -fno-math-errno -fno-trapping-math -fno-strict-aliasing -fPIC -Wno-gnu-statement-expression
%endif
%ifarch %{arm} %{riscv}
%global optflags %{optflags} -O2 -fno-strict-aliasing -fPIC -Wno-gnu-statement-expression
%endif
%global build_ldflags %{build_ldflags} -fPIC

# (tpg) enable PGO build
%ifnarch riscv64 %{arm}
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	Crypt Library for DES, MD5, Blowfish and others
Name:		libxcrypt
Version:	4.4.26
Release:	2
License:	LGPLv2+
Group:		System/Libraries
Url:		https://github.com/besser82/libxcrypt
Source0:	https://github.com/besser82/libxcrypt/archive/%{name}-%{version}.tar.xz
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
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate" \
CXXFLAGS="%{optflags} -fprofile-generate" \
FFLAGS="$CFLAGS" \
FCFLAGS="$CFLAGS" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
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
llvm-profdata merge --output=%{name}-llvm.profdata *.profraw
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw

make clean

# profile-instr-out-of-date and profile-instr-unprofiled are
# caused by the static lib not being used during make check.
# Only the shared lib and everything shared between the shared
# and static lib is profiled
CFLAGS="%{optflags} -fprofile-use=$PROFDATA -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled -Wno-error=backend-plugin" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled -Wno-error=backend-plugin" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA -Wno-error=profile-instr-out-of-date -Wno-error=profile-instr-unprofiled -Wno-error=backend-plugin" \
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

%if 0
# (tpg) convert static archives and object files compiled with LLVM and LTO to ELF format
# taken from https://src.fedoraproject.org/rpms/redhat-rpm-config/blob/rawhide/f/brp-llvm-compile-lto-elf
TMPDIR=$(mktemp -d)

check_convert_bitcode () {
  local file_name=$(realpath ${1})
  local file_type=$(file ${file_name})

  if [[ "${file_type}" == *"LLVM IR bitcode"*  ]]; then
    # check for an indication that the bitcode was
    # compiled with -flto
    llvm-bcanalyzer -dump ${file_name} | grep -xP '.*\-flto((?!-fno-lto).)*' 2>&1 > /dev/null
    if [ $? -eq 0 ]; then
      printf '%s\n' "Compiling LLVM bitcode file ${file_name}."
      # create path to file in temp dir
      # move file to temp dir with llvm .bc extension for clang
      mkdir -p ${TMPDIR}/$(dirname ${file_name})
      mv $file_name ${TMPDIR}/${file_name}.bc
      clang -c %{optflags} -fno-lto -Wno-unused-command-line-argument ${TMPDIR}/${file_name}.bc -o ${file_name}
    fi
  elif [[ "${file_type}" == *"current ar archive"*  ]]; then
    printf '%s\n' "Unpacking ar archive ${file_name} to check for LLVM bitcode components."
    # create archive stage for objects
    local archive_stage=$(mktemp -d)
    local archive=${file_name}
    cd ${archive_stage}
    ar x ${archive}
    for archived_file in $(find -not -type d); do
      check_convert_bitcode ${archived_file}
      printf '%s\n' "Repacking ${archived_file} into ${archive}."
      ar r ${archive} ${archived_file}
    done
    cd ..
  fi
}

printf '$s\n' "Checking for LLVM bitcode artifacts"
for i in $(find %{buildroot} -type f -name "*.[ao]"); do
  check_convert_bitcode ${i}
done
%endif

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
%doc AUTHORS NEWS
%{_includedir}/*.h
/%{_lib}/libcrypt.so
/%{_lib}/libxcrypt.so
%{_libdir}/pkgconfig/*.pc
%doc %{_mandir}/man3/crypt*.3*
%doc %{_mandir}/man5/crypt.5*

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

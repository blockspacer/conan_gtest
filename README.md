# About

modified conan package for gtest:

* uses `git clone`
* supports sanitizers, see [https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-gtest](https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-gtest)
* uses `llvm_tools` conan package in builds with `LLVM_USE_SANITIZER`, see https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-gtest
* uses `llvm_tools` conan package in builds with libc++ (will be instrumented if `LLVM_USE_SANITIZER` enabled)
* etc.

See `test_package/CMakeLists.txt` for usage example

NOTE: use `-s llvm_tools:build_type=Release` during `conan install`

## Before build

```bash
sudo apt-get update

# Tested with clang 6.0 and gcc 7
sudo apt-get -y install clang-6.0 g++-7 gcc-7

# llvm-config binary that coresponds to the same clang you are using to compile
export LLVM_CONFIG=/usr/bin/llvm-config-6.0
$LLVM_CONFIG --cxxflags
```

## Local build

```bash
conan remote add conan-center https://api.bintray.com/conan/conan/conan-center False

export PKG_NAME=conan_gtest/master@conan/stable

(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force $PKG_NAME || true)

CONAN_REVISIONS_ENABLED=1 \
    CONAN_VERBOSE_TRACEBACK=1 \
    CONAN_PRINT_RUN_COMMANDS=1 \
    CONAN_LOGGING_LEVEL=10 \
    GIT_SSL_NO_VERIFY=true \
    conan create . \
      conan/stable \
      -s build_type=Release \
      --profile clang \
      --build missing

CONAN_REVISIONS_ENABLED=1 \
    CONAN_VERBOSE_TRACEBACK=1 \
    CONAN_PRINT_RUN_COMMANDS=1 \
    CONAN_LOGGING_LEVEL=10 \
    conan upload $PKG_NAME \
      --all -r=conan-local \
      -c --retry 3 \
      --retry-wait 10 \
      --force
```

## Build with sanitizers support

Use `-o llvm_tools:enable_msan=True` and `-e *:compile_with_llvm_tools=True` like so:

```bash
CONAN_REVISIONS_ENABLED=1 \
    CONAN_VERBOSE_TRACEBACK=1 \
    CONAN_PRINT_RUN_COMMANDS=1 \
    CONAN_LOGGING_LEVEL=10 \
    GIT_SSL_NO_VERIFY=true \
    conan create . \
      conan/stable \
      -s build_type=Debug \
      -s compiler=clang \
      -s compiler.version=10 \
      -s compiler.libcxx=libc++ \
      -s llvm_tools:compiler=clang \
      -s llvm_tools:compiler.version=6.0 \
      -s llvm_tools:compiler.libcxx=libstdc++11 \
      --profile clang \
      -s llvm_tools:build_type=Release \
      -o llvm_tools:enable_msan=True \
      -o llvm_tools:include_what_you_use=False \
      -e conan_gtest:compile_with_llvm_tools=True \
      -e conan_gtest:enable_llvm_tools=True \
      -e conan_gtest_test_package:compile_with_llvm_tools=True \
      -e conan_gtest_test_package:enable_llvm_tools=True \
      -o conan_gtest:enable_msan=True
```

Perform checks:

```bash
# must exist
find ~/.conan -name libclang_rt.msan_cxx-x86_64.a

# see https://stackoverflow.com/a/47705420
nm -an $(find ~/.conan -name *libc++.so.1 | grep "llvm_tools/master/conan/stable/package/") | grep san
```

Validate that `ldd` points to instrumented `libc++`, see https://stackoverflow.com/a/35197295

Validate that compile log contains `-fsanitize=`

You can test that sanitizer can catch error by adding into `SalutationTest` from `test_package/test_package.cpp` code:

```cpp
  // MSAN test
  int r;
  int* a = new int[10];
  a[5] = 0;
  if (a[r])
    printf("xx\n");
```

## conan Flow

```bash
conan source .
conan install --build missing --profile clang  -s build_type=Release .
conan build . --build-folder=.
conan package --build-folder=. .
conan export-pkg . conan/stable --settings build_type=Release --force --profile clang
conan test test_package conan_gtest/master@conan/stable --settings build_type=Release --profile clang
```

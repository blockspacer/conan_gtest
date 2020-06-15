# About

modified conan package for gtest:

* uses `git clone`
* supports sanitizers, see [https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-gtest](https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-gtest)
* etc.

See `test_package/CMakeLists.txt` for usage example

NOTE: use `-s llvm_tools:build_type=Release` during `conan install`

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

Use `-o llvm_tools:msan=True` and `-e *:compile_with_llvm_tools=True` like so:

```bash
CONAN_REVISIONS_ENABLED=1 \
    CONAN_VERBOSE_TRACEBACK=1 \
    CONAN_PRINT_RUN_COMMANDS=1 \
    CONAN_LOGGING_LEVEL=10 \
    GIT_SSL_NO_VERIFY=true \
    conan create . \
      conan/stable \
      -s build_type=Release \
      --profile clang \
      -o llvm_tools:msan=True \
      -e conan_gtest:compile_with_llvm_tools=True \
      -e conan_gtest:enable_llvm_tools=True \
      --build missing
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

## Build with sanitizers support

Use `-o llvm_tools:msan=True`

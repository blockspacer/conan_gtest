cmake_minimum_required(VERSION 2.8.11)
project(cmake_wrapper)

include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
conan_basic_setup()

option(GTEST_NO_MAIN "Generate google main libraries" OFF)

if(MSVC)
  if(MSVC_VERSION AND MSVC_VERSION GREATER_EQUAL 1910)
    add_definitions(-DGTEST_LANG_CXX11=1 -DGTEST_HAS_TR1_TUPLE=0)
  endif(MSVC_VERSION AND MSVC_VERSION GREATER_EQUAL 1910)
endif(MSVC)

find_package(cmake_helper_utils REQUIRED)

# prefer ASCII for folder names
force_latin_paths() # from cmake_helper_utils (conan package)

# out dirs (CMAKE_*_OUTPUT_DIRECTORY) must be not empty
validate_out_dirs() # from cmake_helper_utils (conan package)

# In-source builds not allowed
validate_out_source_build(WARNING) # from cmake_helper_utils (conan package)

if(COMPILE_WITH_LLVM_TOOLS)
  # force change CMAKE_*_COMPILER and CMAKE_LINKER to clang from conan
  compile_with_llvm_tools() # from cmake_helper_utils (conan package)
endif(COMPILE_WITH_LLVM_TOOLS)


if(ENABLE_MSAN OR ENABLE_TSAN OR ENABLE_ASAN OR ENABLE_UBSAN)
  if(cmake_build_type_tolower MATCHES "release" )
    message(WARNING "Disable sanitizers in Release builds")
  endif()

  # use llvm_tools from conan
  find_program_helper(llvm-symbolizer
    PATHS
      #${CONAN_BIN_DIRS}
      ${CONAN_BIN_DIRS_LLVM_TOOLS}
    NO_SYSTEM_ENVIRONMENT_PATH
    NO_CMAKE_SYSTEM_PATH
    ${ARGUMENTS_UNPARSED_ARGUMENTS}
    REQUIRED
    OUT_VAR LLVM_SYMBOLIZER_PROGRAM
    VERBOSE TRUE
  )

  check_sanitizer_options(
    ENABLE_TSAN ${ENABLE_TSAN}
    ENABLE_ASAN ${ENABLE_ASAN}
    ENABLE_MSAN ${ENABLE_MSAN}
    ENABLE_UBSAN ${ENABLE_UBSAN}
    LLVM_SYMBOLIZER_PROGRAM ${LLVM_SYMBOLIZER_PROGRAM}
  )
endif()

add_subdirectory("source_subfolder")

## ------- sanitize gtest -------

set(LIB_NAME gtest)

if(ENABLE_MSAN)
  message(STATUS "enabling MSAN on ${LIB_NAME}")
  add_msan_static_link(${LIB_NAME})
  add_msan_flags(${LIB_NAME})
endif(ENABLE_MSAN)

if(ENABLE_TSAN)
  message(STATUS "enabling TSAN on ${LIB_NAME}")
  add_tsan_static_link(${LIB_NAME})
  add_tsan_flags(${LIB_NAME})
endif(ENABLE_TSAN)

if(ENABLE_ASAN)
  message(STATUS "enabling ASAN on ${LIB_NAME}")
  add_asan_static_link(${LIB_NAME})
  add_asan_flags(${LIB_NAME})
endif(ENABLE_ASAN)

if(ENABLE_UBSAN)
  message(STATUS "enabling UBSAN on ${LIB_NAME}")
  add_ubsan_static_link(${LIB_NAME})
  add_ubsan_flags(${LIB_NAME})
endif(ENABLE_UBSAN)

## ------- sanitize gmock -------

#if(BUILD_GMOCK)
set(LIB_NAME gmock)

if(ENABLE_MSAN)
  message(STATUS "enabling MSAN on ${LIB_NAME}")
  add_msan_static_link(${LIB_NAME})
  add_msan_flags(${LIB_NAME})
endif(ENABLE_MSAN)

if(ENABLE_TSAN)
  message(STATUS "enabling TSAN on ${LIB_NAME}")
  add_tsan_static_link(${LIB_NAME})
  add_tsan_flags(${LIB_NAME})
endif(ENABLE_TSAN)

if(ENABLE_ASAN)
  message(STATUS "enabling ASAN on ${LIB_NAME}")
  add_asan_static_link(${LIB_NAME})
  add_asan_flags(${LIB_NAME})
endif(ENABLE_ASAN)

if(ENABLE_UBSAN)
  message(STATUS "enabling UBSAN on ${LIB_NAME}")
  add_ubsan_static_link(${LIB_NAME})
  add_ubsan_flags(${LIB_NAME})
endif(ENABLE_UBSAN)
#endif(BUILD_GMOCK)

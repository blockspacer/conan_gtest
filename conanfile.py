import glob
import os
from conans import ConanFile, CMake, tools
from conans.model.version import Version
from conans.errors import ConanInvalidConfiguration

from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment, RunEnvironment, python_requires
from conans.errors import ConanInvalidConfiguration, ConanException
from conans.tools import os_info
import os, re, stat, fnmatch, platform, glob, traceback, shutil
from functools import total_ordering

# if you using python less than 3 use from distutils import strtobool
from distutils.util import strtobool

conan_build_helper = python_requires("conan_build_helper/[~=0.0]@conan/stable")

# Users locally they get the 1.0.0 version,
# without defining any env-var at all,
# and CI servers will append the build number.
# USAGE
# version = get_version("1.0.0")
# BUILD_NUMBER=-pre1+build2 conan export-pkg . my_channel/release
def get_version(version):
    bn = os.getenv("BUILD_NUMBER")
    return (version + bn) if bn else version

class GTestConan(conan_build_helper.CMakePackage):
    name = "conan_gtest"
    description = "Google's C++ test framework"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/googletest"
    repo_url = "https://github.com/google/googletest.git"
    version = get_version("stable")
    commit = "0a3a3a845e136a9a6ccd8e9b924b848840f22b7b"
    patch_version = "1.10.0"
    license = "BSD-3-Clause"
    topics = ("conan", "gtest", "testing", "google-testing", "unit-test")
    exports_sources = ["LICENSE", "VERSION", "*.md", "include/*", "src/*",
                       "cmake/*", "examples/*", "CMakeLists.txt", "tests/*", "benchmarks/*",
                       "scripts/*", "tools/*", "codegen/*", "assets/*",
                       "assets/configuration_files/*", "assets/icu/*", "assets",
                       "docs/*", "licenses/*", "patches/*", "resources/*",
                       "submodules/*", "thirdparty/*", "third-party/*",
                       "third_party/*", "gtest/*", "CMakeLists.txt", "patches/*"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "enable_ubsan": [True, False],
        "enable_asan": [True, False],
        "enable_msan": [True, False],
        "enable_tsan": [True, False],
        "shared": [True, False],
        "build_gmock": [True, False],
        "fPIC": [True, False],
        "no_main": [True, False],
        "debug_postfix": "ANY",
        "hide_symbols": [True, False]
    }

    default_options = {
        "enable_ubsan": False,
        "enable_asan": False,
        "enable_msan": False,
        "enable_tsan": False,
        "shared": False,
        "build_gmock": True,
        "fPIC": True,
        "no_main": False,
        "debug_postfix": 'd',
        "hide_symbols": False
    }
    _source_subfolder = "source_subfolder"

    #@property
    #def _source_dir(self):
    #    return "."

    #@property
    #def _build_dir(self):
    #    return "."

    # sets cmake variables required to use clang 10 from conan
    def _is_compile_with_llvm_tools_enabled(self):
      return self._environ_option("COMPILE_WITH_LLVM_TOOLS", default = 'false')

    # installs clang 10 from conan
    def _is_llvm_tools_enabled(self):
      return self._environ_option("ENABLE_LLVM_TOOLS", default = 'false')

    @property
    def _postfix(self):
        return self.options.debug_postfix if self.settings.build_type == "Debug" else ""

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.build_type != "Debug":
            del self.options.debug_postfix

    def configure(self):
        lower_build_type = str(self.settings.build_type).lower()

        if lower_build_type != "release" and not self._is_llvm_tools_enabled():
            self.output.warn('enable llvm_tools for Debug builds')

        if self._is_compile_with_llvm_tools_enabled() and not self._is_llvm_tools_enabled():
            raise ConanInvalidConfiguration("llvm_tools must be enabled")

        if self.options.enable_ubsan \
           or self.options.enable_asan \
           or self.options.enable_msan \
           or self.options.enable_tsan:
            if not self._is_llvm_tools_enabled():
                raise ConanInvalidConfiguration("sanitizers require llvm_tools")

        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version.value) <= "12":
                raise ConanInvalidConfiguration("Google Test {} does not support Visual Studio <= 12".format(self.version))

    def build_requirements(self):
        self.build_requires("cmake_platform_detection/master@conan/stable")
        self.build_requires("cmake_build_options/master@conan/stable")
        self.build_requires("cmake_helper_utils/master@conan/stable")

        if self.options.enable_tsan \
            or self.options.enable_msan \
            or self.options.enable_asan \
            or self.options.enable_ubsan:
          self.build_requires("cmake_sanitizers/master@conan/stable")

        # provides clang-tidy, clang-format, IWYU, scan-build, etc.
        if self._is_llvm_tools_enabled():
          self.build_requires("llvm_tools/master@conan/stable")

    def source(self):
        #tools.get(**self.conan_data["sources"][self.version])
        #extracted_dir = "googletest-release-" + self.version
        #os.rename(extracted_dir, self._source_subfolder)
        self.run('git clone -b {} --progress --depth 100 --recursive --recurse-submodules {} {}'.format("main", self.repo_url, self._source_subfolder))
        with tools.chdir(self._source_subfolder):
          if self.commit:
            self.run('git checkout {}'.format(self.commit))

    def _configure_cmake(self):
        cmake = CMake(self)
        if self.settings.build_type == "Debug":
            cmake.definitions["CUSTOM_DEBUG_POSTFIX"] = self.options.debug_postfix
        if self.settings.os == "Windows" and self.settings.get_safe("compiler.runtime"):
            cmake.definitions["gtest_force_shared_crt"] = "MD" in str(self.settings.compiler.runtime)
        cmake.definitions["BUILD_GMOCK"] = self.options.build_gmock
        cmake.definitions["GTEST_NO_MAIN"] = self.options.no_main
        if self.settings.os == "Windows" and self.settings.compiler == "gcc":
            cmake.definitions["gtest_disable_pthreads"] = True
        cmake.definitions["gtest_hide_internal_symbols"] = self.options.hide_symbols

        cmake.definitions["ENABLE_UBSAN"] = 'ON'
        if not self.options.enable_ubsan:
            cmake.definitions["ENABLE_UBSAN"] = 'OFF'

        cmake.definitions["ENABLE_ASAN"] = 'ON'
        if not self.options.enable_asan:
            cmake.definitions["ENABLE_ASAN"] = 'OFF'

        cmake.definitions["ENABLE_MSAN"] = 'ON'
        if not self.options.enable_msan:
            cmake.definitions["ENABLE_MSAN"] = 'OFF'

        cmake.definitions["ENABLE_TSAN"] = 'ON'
        if not self.options.enable_tsan:
            cmake.definitions["ENABLE_TSAN"] = 'OFF'

        self.add_cmake_option(cmake, "COMPILE_WITH_LLVM_TOOLS", self._is_compile_with_llvm_tools_enabled())

        cmake.configure()
        return cmake

    def build(self):
        with tools.vcvars(self.settings, only_diff=False): # https://github.com/conan-io/conan/issues/6577
            #for patch in self.conan_data["patches"][self.patch_version]:
            #    tools.patch(**patch)
            tools.patch(patch_file = "patches/gtest-1.10.0.patch", base_path = self._source_subfolder)
            cmake = self._configure_cmake()
            cmake.build()
            cmake.install()

    def package(self):
        with tools.vcvars(self.settings, only_diff=False): # https://github.com/conan-io/conan/issues/6577
            self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
            # TODO: file INSTALL cannot set permissions on "/usr/local/include"
            #cmake = self._configure_cmake()
            #cmake.install()
            tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
            tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
            for pdb_file in glob.glob(os.path.join(self.package_folder, "lib", "*.pdb")):
                os.unlink(pdb_file)

    def package_id(self):
        del self.info.options.no_main

    def package_info(self):
        if self.options.build_gmock:
            gmock_libs = ['gmock', 'gtest'] if self.options.no_main else ['gmock_main', 'gmock', 'gtest']
            self.cpp_info.libs = ["{}{}".format(lib, self._postfix) for lib in gmock_libs]
        else:
            gtest_libs = ['gtest'] if self.options.no_main else ['gtest_main' , 'gtest']
            self.cpp_info.libs = ["{}{}".format(lib, self._postfix) for lib in gtest_libs]

        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("pthread")

        if self.options.shared:
            self.cpp_info.defines.append("GTEST_LINKED_AS_SHARED_LIBRARY=1")

        if self.settings.compiler == "Visual Studio":
            if Version(self.settings.compiler.version.value) >= "15":
                self.cpp_info.defines.append("GTEST_LANG_CXX11=1")
                self.cpp_info.defines.append("GTEST_HAS_TR1_TUPLE=0")
        #self.cpp_info.names["cmake_find_package"] = "GTest"
        #self.cpp_info.names["cmake_find_package_multi"] = "GTest"

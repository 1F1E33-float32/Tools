cmake_minimum_required(VERSION 3.10)
project(krkrtool LANGUAGES CXX)

if(MSVC)
  if(NOT CMAKE_SIZEOF_VOID_P EQUAL 4)
    message(WARNING
      "This project is intended for 32-bit (x86) builds. "
      "Please reconfigure with e.g. -A Win32.")
  endif()
else()
  message(FATAL_ERROR "This CMakeLists is designed for MSVC only.")
endif()

include_directories("${CMAKE_SOURCE_DIR}/src/compat")

set(COMMON_SOURCES
  src/compat/tp_stub.cpp
  src/compat/winversion_v100.def
)

set(COMMON_CXX_OPTS /Gy /Gw)
set(COMMON_LINK_OPTS_RELEASE /OPT:REF)
set(COMMON_LIBS gdi32)

add_library(krkr_hxv4_dumphash SHARED
  src/krkr_hxv4_dumphash.cpp
  ${COMMON_SOURCES}
)

target_compile_definitions(krkr_hxv4_dumphash PRIVATE
  $<$<CONFIG:Debug>:_DEBUG>
  $<$<CONFIG:Release>:NDEBUG>
)

target_compile_options(krkr_hxv4_dumphash PRIVATE
  ${COMMON_CXX_OPTS}
  $<$<CONFIG:Debug>:/Zi>               # debug info
  $<$<CONFIG:Release>:/O2 /GL>         # optimize + LTO
)

target_link_options(krkr_hxv4_dumphash PRIVATE
  $<$<CONFIG:Debug>:/DEBUG>
  $<$<CONFIG:Release>:${COMMON_LINK_OPTS_RELEASE}>
)

target_link_libraries(krkr_hxv4_dumphash PRIVATE ${COMMON_LIBS})

set_target_properties(krkr_hxv4_dumphash PROPERTIES
  OUTPUT_NAME         "version"
  ARCHIVE_OUTPUT_NAME "version"
  PDB_NAME            "version"
)
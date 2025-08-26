cmake_minimum_required(VERSION 3.10)
project(cat_system_crypto LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 优先使用版本无关的 FindPython（会生成 Python::Module）
find_package(Python QUIET COMPONENTS Interpreter Development.Module)

# 某些环境只有 FindPython3，就回退并做别名，提供 Python::Module 给 nanobind 用
if(NOT Python_FOUND)
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
    if(TARGET Python3::Module AND NOT TARGET Python::Module)
        add_library(Python::Module ALIAS Python3::Module)
    endif()
    if(TARGET Python3::Interpreter AND NOT TARGET Python::Interpreter)
        add_library(Python::Interpreter ALIAS Python3::Interpreter)
    endif()
    if(TARGET Python3::Python AND NOT TARGET Python::Python)
        add_library(Python::Python ALIAS Python3::Python)
    endif()
endif()

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../../../../_ThirdParty/nanobind
    ${CMAKE_CURRENT_BINARY_DIR}/nanobind)

nanobind_add_module(cat_system_crypto cat_system_crypto.cpp)
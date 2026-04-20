cmake_minimum_required(VERSION 3.10)
project(SignVerseWBMPC)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# If we were using Eigen, we would find it here:
# find_package(Eigen3 REQUIRED)
# include_directories(${EIGEN3_INCLUDE_DIR})

# For production we compile this as a shared library that ctypes can load.
add_library(wbmpc_solver SHARED optimizer.cpp)

# Optimization flags for High-Performance
target_compile_options(wbmpc_solver PRIVATE -O3 -ffast-math)

# Note: The output needs to be named optimizer.so or optimizer.dll
if(WIN32)
    set_target_properties(wbmpc_solver PROPERTIES PREFIX "" SUFFIX ".dll" OUTPUT_NAME "optimizer")
else()
    set_target_properties(wbmpc_solver PROPERTIES PREFIX "" SUFFIX ".so" OUTPUT_NAME "optimizer")
endif()

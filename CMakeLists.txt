cmake_minimum_required(VERSION 3.10)
project(TOMS)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g -Wall -DDEBUG")

include_directories(${CMAKE_SOURCE_DIR}/headers)
include_directories(${CMAKE_SOURCE_DIR}/resources)
include_directories(${CMAKE_SOURCE_DIR}/parsers)
include_directories(${CMAKE_SOURCE_DIR}/dynamic_resource_generators)
include_directories(${CMAKE_SOURCE_DIR}/gen_task_src)
add_executable(gastask
    gen_task_src/gastask.c
    gen_task_src/GA.c
    gen_task_src/task.c
    gen_task_src/util.c
    gen_task_src/report.c

    resources/cloud.c
    resources/cpu.c
    resources/mem.c
    resources/net_commander.c
    resources/network.c
    resources/offloadingratio.c
    
    parsers/conf.c
    parsers/conf_gastask.c
)

target_link_libraries(gastask m)

add_executable(gasgen
    gen_task_src/gasgen.c
    gen_task_src/util.c

    dynamic_resource_generators/gen_network.c
    dynamic_resource_generators/gen_netcommander.c
    dynamic_resource_generators/gen_task.c

    resources/mem.c
    resources/cloud.c
    resources/net_commander.c
    resources/network.c
    resources/offloadingratio.c

    parsers/conf.c
    parsers/conf_gasgen.c
)

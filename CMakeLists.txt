cmake_minimum_required(VERSION 3.10)
project(TOMS)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g -Wall -DDEBUG")

add_executable(gastask
    gastask.c
    GA.c
    task.c
    cpu.c
    mem.c
    util.c
    conf.c
    conf_gastask.c
    report.c
    cloud.c
    offloadingratio.c
    network.c
    net_commander.c
)

target_link_libraries(gastask m)

add_executable(gasgen
    gasgen.c
    gen_task.c
    mem.c
    util.c
    conf.c
    conf_gasgen.c
    gen_network.c
    gen_netcommander.c
    cloud.c
    offloadingratio.c
    network.c
    net_commander.c
)

# Co-TOMS (Co-optimizing Task Offloading, Memory placement, and voltage Scaling)

This project performs real-time task scheduling based on steady-state genetic algorithms in order to save power consumptions in CPU, memory, and network subsystems with deadline constraints.

Co-TOMS considers three energy-saving techniques, DVFS (dynamic voltage/frequency scaling), hybrid memory placement, and task offloading to edge servers, across different system layers.

Two executables included in this project, which can simulate Co-TOMS in comparison with DVFS, Offloading, and basic configurations.
- `gasgen`: task generation tool based on CPU and total utilization
- `gastask`: scheduling scheme generator based on GA

For comparison purposes, our basic simulator supporting dynamic voltage scaling (DVS) and hybrid memory (HM) can be downloaded at https://github.com/oslab-ewha/simrts.

## Build
To build `gastask` and `gasgen`, use CMake:
```
$ mkdir -p build && cd build
$ cmake ..
$ make
```

## Run
- Create a new configuration file. Refer to `gastask.conf.tmpl`.
- run `gasgen`
```
# ./gasgen gastask.conf
```
- Tasks list will be generated into <code>task_generated.txt</code> <code>network_generated.txt</code> <code>network_commander_generated.txt</code>according to gastask.conf
- paste <code>task_generated.txt</code> into the task section of gastask.conf 
- paste <code>network_generated.txt</code> into the network section of gastask.conf
- paste <code>network_commander_generated.txt</code> into the net_commander_ section of gastask.conf
- run gastask
```
# ./gastask gastask.conf
```
- scheduling information is generated in <code>task.txt</code>, which can be used as an input to simrts.

## Batch run
- `run.sh` performs all procedures in batch
  - Before executing run.sh,  ./tmp folder should be generated in root.


## Data Set

There are two types of data set to perform the simulations of Co-TOMS.

- Synthetic workload: 
  - [20% CPU Utilization Workload](dataset/synthetic/cpu_20):
  - [30% CPU Utilization Workload](dataset/synthetic/cpu_30):
  - [40% CPU Utilization Workload](dataset/synthetic/cpu_40):
  - [50% CPU Utilization Workload](dataset/synthetic/cpu_50):
  - [60% CPU Utilization Workload](dataset/synthetic/cpu_60):
  - [70% CPU Utilization Workload](dataset/synthetic/cpu_70):
  - [80% CPU Utilization Workload](dataset/synthetic/cpu_80):
  - [90% CPU Utilization Workload](dataset/synthetic/cpu_90):

- Realistic worload:
  - [Robotic Highway Safety Marker (RSM)](dataset/realistic/RSM): real-time task set for the actions of mobile robots that carry safety markers in a highway for road construction safety
  - [IoT](dataset/realistic/IoT): real-time task set for the actions of a controller in industry machine hands

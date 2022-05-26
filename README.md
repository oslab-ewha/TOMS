# TOVS (Task Offloading & Voltage Scaling)
Edge Computing &amp; Voltage Scaling

This project demonstrates that a GA(genetic algorithm) approach can provide power-efficient scheduling for real-time tasks that makes use of DVS(dynamic voltage scaling) and edge computing. 

Two executagles included in this project.
- `gasgen`: task generation tool based on CPU and total utilization
- `gastask`: scheduling scheme generator based on GA

For comparison purposes, our basic simulator supporting dynamic voltage scaling (DVS) and hybrid memory (HM) can be downloaded at https://github.com/oslab-ewha/simrts.

## Build
Just make to build gastask
```
# make
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
  - Before do `run.sh`, it need `./tmp` folder in root 
  - use `run.sh` for mac, use `run2.sh` for window


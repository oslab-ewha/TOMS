#!/bin/bash

# Get arguments
utilTarget=$1
utilCpu=$2
networkUp=$3
networkDown=$4
seed=$5

if [ $# -lt 3 ]; then
    echo "Usage: run_candy.sh <util> <util cpu> <network_up> <network_down> <seed>"
    exit 1
fi

# Create output directories
OUTPUT=./tmp/output_$utilTarget+$$
mkdir -p $OUTPUT
mkdir -p $OUTPUT/conf
mkdir -p $OUTPUT/report
mkdir -p $OUTPUT/task

# Function to create configuration for each algorithm
create_config() {
    local conf_file=$1
    local tee_enabled=$2
    local offloading_enabled=$3
    local dvfs_enabled=$4

    # Copy the base configuration
    cp candy_cycle.conf "$conf_file"

    # Modify TEE setting
    sed -i "s/^*TEE\n1/*TEE\n$tee_enabled/" "$conf_file"

    # Modify CPU frequency options if DVFS is disabled
    if [ "$dvfs_enabled" = "false" ]; then
        sed -i '/*cpufreq/,/0.125/c\# wcet_scale power_active power_idle\n*cpufreq\n1    100    1' "$conf_file"
    fi

    # Modify offloading if disabled
    if [ "$offloading_enabled" = "false" ]; then
        sed -i 's/*offloadingratio\n0\n1/*offloadingratio\n0/' "$conf_file"
        # Also modify all tasks to be local
        sed -i 's/\t1$/\t0/' "$conf_file"
    fi
}

# Initialize the output file (empty, headers will be added later)
> $OUTPUT/output_$utilTarget+$networkUp.txt

# Function to run an experiment
run_experiment() {
    local name=$1
    local tee=$2
    local offloading=$3
    local dvfs=$4

    local conf_file=$OUTPUT/conf/gastask_${name}_$utilTarget+$$.conf

    create_config "$conf_file" "$tee" "$offloading" "$dvfs"
    
    echo "*$name" >> $OUTPUT/output_$utilTarget+$networkUp.txt
    ./gastask -s $seed "$conf_file" > $OUTPUT/tmp_output.txt
    cat $OUTPUT/tmp_output.txt >> $OUTPUT/output_$utilTarget+$networkUp.txt

    mv task.txt $OUTPUT/task/task_$utilTarget+$networkUp+${name}.txt 2>/dev/null || true
    mv report.txt $OUTPUT/report/report_$utilTarget+$networkUp+${name}.txt 2>/dev/null || true
}

# Run all algorithms
run_experiment "CO-DMO-CT" 1 true true
run_experiment "CO-DMO" 0 true true
run_experiment "Offloading" 0 true false
run_experiment "DVS" 0 false true
run_experiment "Baseline" 0 false false

# Clean up
rm -f $OUTPUT/tmp_output.txt

echo "Simulation completed. Results saved in $OUTPUT"

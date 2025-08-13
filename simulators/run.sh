#!/bin/bash
# run.sh 
# Description:
# This script automates the simulation of various optimization strategies 
# for real-time task execution in Industrial IoT (IIoT) environments. 
# It generates configurations, executes simulations, and organizes results 
# for different scenarios, including CO-DMO-CT, CO-DMO, Offloading, DVS, 
# and Baseline.
#
# Usage:
# ./run.sh <util> <util cpu> <network_up> <network_down> <seed>
#
# Parameters:
# <util>          - Target utilization for the simulation.
# <util cpu>      - CPU utilization for the simulation.
# <network_up>    - Uplink network bandwidth (Mbps).
# <network_down>  - Downlink network bandwidth (Mbps).
# <seed>          - Random seed for reproducibility.

function usage() {
    cat <<EOF
Usage: run.sh <util> <util cpu> <network_up> <network_down> <seed>
EOF
}

if [ $# -lt 3 ]; then
    usage
    exit 1
fi

GASTASK=`./gastask`
GASGEN=`./gasgen`

utilTarget=$1
utilCpu=$2
networkUp=$3
networkDown=$4
seed=$5

# tmp 디렉토리 생성
mkdir -p ./tmp

# 기본 설정 생성 함수
create_base_config() {
    local config_file=$1
    local tee_enabled=$2
    local offloading_enabled=$3
    local dvfs_enabled=$4
    
    cat > $config_file << EOF
# max_generations n_populations cutoff penalty
*genetic
10000 100 1.5 1.5

# wcet_min wcet_max mem_total util_cpu util_target n_tasks task_size_min task_size_max input_size_min input_size_max output_size_min output_size_max
*gentask
100 1000 2000 $utilCpu $utilTarget 100 4000 6000 2000 4000 2000 4000

# uplink_min uplink_max downlink_min downlink_max n_networks
*gennetwork
$networkUp $networkUp $networkDown $networkDown 100

# intercept_out_min intercept_out_max intercept_in_min intercept_in_max n_net_commanders
*gennetcommander
1 5 5 7 100

# wcet_scale power_active power_idle
*cpufreq
EOF

    if [ "$dvfs_enabled" = "true" ]; then
        cat >> $config_file << EOF
1    100    1
0.5  25   0.25
0.25 6.25 0.0625
0.125 1.5625 0.015625
EOF
    else
        cat >> $config_file << EOF
1    100    1
EOF
    fi

    cat >> $config_file << EOF

# type max_capacity wcet_scale power_active power_idle
*mem
dram  1000 1    0.01   0.01
nvram 1000 0.8  0.01   0.0001

# type computation_power power_active power_idle max_capacity offloading_limit
*cloud
mec  4   400   100   100000   1.0

# offloading_ratio 
*offloadingratio
EOF

    if [ "$offloading_enabled" = "true" ]; then
        cat >> $config_file << EOF
0
1
EOF
    else
        cat >> $config_file << EOF
0
EOF
    fi

    cat >> $config_file << EOF

# TEE 
*TEE
$tee_enabled

# uplink_data_rate downlink_data_rate
*network
EOF

    # gasgen을 실행하여 네트워크 및 태스크 생성
    ./gasgen $config_file
    cat ./network_generated.txt >> $config_file

    cat >> $config_file << EOF

# intercept_out intercept_in
*netcommander
EOF
    cat ./network_commander_generated.txt >> $config_file

    cat >> $config_file << EOF

# wcet period memreq mem_active_ratio task_size input_size output_size offloading_bool
*task
EOF
    cat ./task_generated.txt >> $config_file
}

# 출력 디렉토리 생성
OUTPUT=./tmp/output_$utilTarget+$$
mkdir -p $OUTPUT
mkdir -p $OUTPUT/conf
mkdir -p $OUTPUT/gen
mkdir -p $OUTPUT/report
mkdir -p $OUTPUT/task
touch $OUTPUT/output_$utilTarget+$networkUp.txt

# 1. CO-DMO-CT (TEE=1, All optimizations enabled)
echo "*CO-DMO-CT" >> $OUTPUT/output_$utilTarget+$networkUp.txt
gastask_conf_1=$OUTPUT/conf/gastask_co-dmo-ct_$utilTarget+$$.conf
create_base_config $gastask_conf_1 1 true true
./gastask -s $seed $gastask_conf_1 | tee -a $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task/task_$utilTarget+$networkUp+co-dmo-ct.txt
mv report.txt $OUTPUT/report/report_$utilTarget+$networkUp+co-dmo-ct.txt 2>/dev/null || true

# 2. CO-DMO (TEE=0, All optimizations enabled)
echo "" >> $OUTPUT/output_$utilTarget+$networkUp.txt
echo "*CO-DMO" >> $OUTPUT/output_$utilTarget+$networkUp.txt
gastask_conf_2=$OUTPUT/conf/gastask_co-dmo_$utilTarget+$$.conf
create_base_config $gastask_conf_2 0 true true
./gastask -s $seed $gastask_conf_2 | tee -a $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task/task_$utilTarget+$networkUp+co-dmo.txt
mv report.txt $OUTPUT/report/report_$utilTarget+$networkUp+co-dmo.txt 2>/dev/null || true

# 3. Offloading (TEE=0, Only offloading)
echo "" >> $OUTPUT/output_$utilTarget+$networkUp.txt
echo "*Offloading" >> $OUTPUT/output_$utilTarget+$networkUp.txt
gastask_conf_3=$OUTPUT/conf/gastask_offloading_$utilTarget+$$.conf
create_base_config $gastask_conf_3 0 true false
./gastask -s $seed $gastask_conf_3 | tee -a $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task/task_$utilTarget+$networkUp+offloading.txt
mv report.txt $OUTPUT/report/report_$utilTarget+$networkUp+offloading.txt 2>/dev/null || true

# 4. DVS (TEE=0, Only DVFS)
echo "" >> $OUTPUT/output_$utilTarget+$networkUp.txt
echo "*DVS" >> $OUTPUT/output_$utilTarget+$networkUp.txt
gastask_conf_4=$OUTPUT/conf/gastask_dvs_$utilTarget+$$.conf
create_base_config $gastask_conf_4 0 false true
./gastask -s $seed $gastask_conf_4 | tee -a $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task/task_$utilTarget+$networkUp+dvs.txt
mv report.txt $OUTPUT/report/report_$utilTarget+$networkUp+dvs.txt 2>/dev/null || true

# 5. Baseline (TEE=0, No optimizations)
echo "" >> $OUTPUT/output_$utilTarget+$networkUp.txt
echo "*Baseline" >> $OUTPUT/output_$utilTarget+$networkUp.txt
gastask_conf_5=$OUTPUT/conf/gastask_baseline_$utilTarget+$$.conf
create_base_config $gastask_conf_5 0 false false
./gastask -s $seed $gastask_conf_5 | tee -a $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task/task_$utilTarget+$networkUp+baseline.txt
mv report.txt $OUTPUT/report/report_$utilTarget+$networkUp+baseline.txt 2>/dev/null || true

# 정리
mv ./task_generated.txt $OUTPUT/gen/gen_task_generated_$utilTarget+$$.txt 2>/dev/null || true
mv ./network_commander_generated.txt $OUTPUT/gen/gen_network_commander_generated_$utilTarget+$$.txt 2>/dev/null || true
mv ./network_generated.txt $OUTPUT/gen/gen_network_generated_$utilTarget+$$.txt 2>/dev/null || true

echo "Simulation completed. Results saved in $OUTPUT"

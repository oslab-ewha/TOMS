#!/bin/bash
# run_iot.sh
# Description:
# Automates simulations for various optimization strategies in IIoT.
# Uses *task section from iot_cycle.conf directly (no generated tasks).
#
# Usage:
# ./run_iot.sh <network_up> <network_down> <seed>
#
# Parameters:
# <network_up>    - Uplink network bandwidth (Mbps)
# <network_down>  - Downlink network bandwidth (Mbps)
# <seed>          - Random seed for reproducibility

function usage() {
    cat <<EOF
Usage: run_iot.sh <network_up> <network_down> <seed>
EOF
}

if [ $# -lt 3 ]; then
    usage
    exit 1
fi

GASTASK=./gastask
GASGEN=./gasgen

networkUp=$1
networkDown=$2
seed=$3

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
100 1000 2000 0.8 0.8 100 4000 6000 2000 4000 2000 4000

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

    # gasgen 실행하여 네트워크/네트워크 커맨더 생성
    $GASGEN $config_file
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
    # iot_cycle.conf의 *task 이후 내용 가져오기
    grep -A 1000 '^\*task' ./iot_cycle.conf | tail -n +2 >> $config_file
}

# 출력 디렉토리 생성
OUTPUT=./tmp/output_$$
mkdir -p $OUTPUT $OUTPUT/conf $OUTPUT/gen $OUTPUT/report $OUTPUT/task
touch $OUTPUT/output.txt

# 1. CO-DMO-CT
echo "*CO-DMO-CT" >> $OUTPUT/output.txt
conf1=$OUTPUT/conf/gastask_co-dmo-ct.conf
create_base_config $conf1 1 true true
$GASTASK -s $seed $conf1 | tee -a $OUTPUT/output.txt
mv task.txt $OUTPUT/task/task_co-dmo-ct.txt
mv report.txt $OUTPUT/report/report_co-dmo-ct.txt 2>/dev/null || true

# 2. CO-DMO
echo "" >> $OUTPUT/output.txt
echo "*CO-DMO" >> $OUTPUT/output.txt
conf2=$OUTPUT/conf/gastask_co-dmo.conf
create_base_config $conf2 0 true true
$GASTASK -s $seed $conf2 | tee -a $OUTPUT/output.txt
mv task.txt $OUTPUT/task/task_co-dmo.txt
mv report.txt $OUTPUT/report/report_co-dmo.txt 2>/dev/null || true

# 3. Offloading
echo "" >> $OUTPUT/output.txt
echo "*Offloading" >> $OUTPUT/output.txt
conf3=$OUTPUT/conf/gastask_offloading.conf
create_base_config $conf3 0 true false
$GASTASK -s $seed $conf3 | tee -a $OUTPUT/output.txt
mv task.txt $OUTPUT/task/task_offloading.txt
mv report.txt $OUTPUT/report/report_offloading.txt 2>/dev/null || true

# 4. DVS
echo "" >> $OUTPUT/output.txt
echo "*DVS" >> $OUTPUT/output.txt
conf4=$OUTPUT/conf/gastask_dvs.conf
create_base_config $conf4 0 false true
$GASTASK -s $seed $conf4 | tee -a $OUTPUT/output.txt
mv task.txt $OUTPUT/task/task_dvs.txt
mv report.txt $OUTPUT/report/report_dvs.txt 2>/dev/null || true

# 5. Baseline
echo "" >> $OUTPUT/output.txt
echo "*Baseline" >> $OUTPUT/output.txt
conf5=$OUTPUT/conf/gastask_baseline.conf
create_base_config $conf5 0 false false
$GASTASK -s $seed $conf5 | tee -a $OUTPUT/output.txt
mv task.txt $OUTPUT/task/task_baseline.txt
mv report.txt $OUTPUT/report/report_baseline.txt 2>/dev/null || true

# 정리
mv ./network_commander_generated.txt $OUTPUT/gen/gen_network_commander_generated.txt 2>/dev/null || true
mv ./network_generated.txt $OUTPUT/gen/gen_network_generated.txt 2>/dev/null || true

echo "Simulation completed. Results saved in $OUTPUT"

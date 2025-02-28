#!/bin/bash

# set experimental values
workloads=(0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1.0 1.05 1.1 1.15 1.2)
networkUp=120
networkDown=120
seed=0
iterations=3

output_dir="./tmp"

# set the name of the result_file
result_file="$output_dir/result_${networkUp}_${networkDown}_${iterations}.txt"

echo "Workload Section Power Util CPU_Power Memory_Power Network_Power Offloading_Ratio CPU_Frequency_1 CPU_Frequency_0.5 CPU_Frequency_0.25 CPU_Frequency_0.125" > $result_file

# conduct experiments according to workload
for workload in "${workloads[@]}"; do
    echo "Running workload: $workload"
    # set utilCpu
    utilCpu=$(echo "$workload - 0.025" | bc)

    # Initializing variables for calculating averages
    declare -A sums
    declare -A counts

    sections=("Tovs" "Offloading" "DVFS" "Nothing")
    metrics=("Power" "Util" "CPU_Power" "Memory_Power" "Network_Power" "Offloading_Ratio" "CPU_Frequency_1" "CPU_Frequency_0.5" "CPU_Frequency_0.25" "CPU_Frequency_0.125")

    for section in "${sections[@]}"; do
        for metric in "${metrics[@]}"; do
            sums["$section $metric"]=0
        done
        counts["$section"]=0
    done

    for ((i = 1; i <= iterations; i++)); do
        echo "Iteration $i for workload $workload..."

        # run "run.sh"
        output=$(./run.sh $workload $utilCpu $networkUp $networkDown $seed)

        # Extract values by section
        for section in "${sections[@]}"; do
            case $section in
                "Tovs")
                    power=$(echo "$output" | sed -n '3p' | awk '{print $2}')
                    util=$(echo "$output" | sed -n '3p' | awk '{print $4}')
                    cpu_power=$(echo "$output" | sed -n '4p' | awk '{print $3}')
                    memory_power=$(echo "$output" | sed -n '4p' | awk '{print $6}')
                    network_power=$(echo "$output" | sed -n '4p' | awk '{print $9}')
                    ratio=$(echo "$output" | sed -n '5p' | awk '{print $3}')
                    freq_1=$(echo "$output" | sed -n '8p' | awk '{print $1}')
                    freq_0_5=$(echo "$output" | sed -n '8p' | awk '{print $2}')
                    freq_0_25=$(echo "$output" | sed -n '8p' | awk '{print $3}')
                    freq_0_125=$(echo "$output" | sed -n '8p' | awk '{print $4}')
                    ;;
                "Offloading")
                    power=$(echo "$output" | sed -n '11p' | awk '{print $2}')
                    util=$(echo "$output" | sed -n '11p' | awk '{print $4}')
                    cpu_power=$(echo "$output" | sed -n '12p' | awk '{print $3}')
                    memory_power=$(echo "$output" | sed -n '12p' | awk '{print $6}')
                    network_power=$(echo "$output" | sed -n '12p' | awk '{print $9}')
                    ratio=$(echo "$output" | sed -n '13p' | awk '{print $3}')
                    freq_1=$(echo "$output" | sed -n '16p' | awk '{print $1}')
                    freq_0_5=$(echo "$output" | sed -n '16p' | awk '{print $2}')
                    freq_0_25=$(echo "$output" | sed -n '16p' | awk '{print $3}')
                    freq_0_125=$(echo "$output" | sed -n '16p' | awk '{print $4}')
                    ;;
                "DVFS")
                    power=$(echo "$output" | sed -n '19p' | awk '{print $2}')
                    util=$(echo "$output" | sed -n '19p' | awk '{print $4}')
                    cpu_power=$(echo "$output" | sed -n '20p' | awk '{print $3}')
                    memory_power=$(echo "$output" | sed -n '20p' | awk '{print $6}')
                    network_power=$(echo "$output" | sed -n '20p' | awk '{print $9}')
                    ratio=$(echo "$output" | sed -n '21p' | awk '{print $3}')
                    freq_1=$(echo "$output" | sed -n '24p' | awk '{print $1}')
                    freq_0_5=$(echo "$output" | sed -n '24p' | awk '{print $2}')
                    freq_0_25=$(echo "$output" | sed -n '24p' | awk '{print $3}')
                    freq_0_125=$(echo "$output" | sed -n '24p' | awk '{print $4}')
                    ;;
		"Nothing")
                    power=$(echo "$output" | sed -n '27p' | awk '{print $2}')
                    util=$(echo "$output" | sed -n '27p' | awk '{print $4}')
                    cpu_power=$(echo "$output" | sed -n '28p' | awk '{print $3}')
                    memory_power=$(echo "$output" | sed -n '28p' | awk '{print $6}')
                    network_power=$(echo "$output" | sed -n '28p' | awk '{print $9}')
                    ratio=$(echo "$output" | sed -n '29p' | awk '{print $3}')
                    freq_1=$(echo "$output" | sed -n '32p' | awk '{print $1}')
                    freq_0_5=$(echo "$output" | sed -n '32p' | awk '{print $2}')
                    freq_0_25=$(echo "$output" | sed -n '32p' | awk '{print $3}')
                    freq_0_125=$(echo "$output" | sed -n '32p' | awk '{print $4}')
                    ;;
            esac

            # calculate sum of values
            if [[ -n "$power" ]]; then
                sums["$section Power"]=$(echo "${sums["$section Power"]} + $power" | bc)
                sums["$section Util"]=$(echo "${sums["$section Util"]} + $util" | bc)
                sums["$section CPU_Power"]=$(echo "${sums["$section CPU_Power"]} + $cpu_power" | bc)
                sums["$section Memory_Power"]=$(echo "${sums["$section Memory_Power"]} + $memory_power" | bc)
                sums["$section Network_Power"]=$(echo "${sums["$section Network_Power"]} + $network_power" | bc)
                sums["$section Offloading_Ratio"]=$(echo "${sums["$section Offloading_Ratio"]} + $ratio" | bc)
                sums["$section CPU_Frequency_1"]=$(echo "${sums["$section CPU_Frequency_1"]} + $freq_1" | bc)
                sums["$section CPU_Frequency_0.5"]=$(echo "${sums["$section CPU_Frequency_0.5"]} + $freq_0_5" | bc)
                sums["$section CPU_Frequency_0.25"]=$(echo "${sums["$section CPU_Frequency_0.25"]} + $freq_0_25" | bc)
                sums["$section CPU_Frequency_0.125"]=$(echo "${sums["$section CPU_Frequency_0.125"]} + $freq_0_125" | bc)
                counts["$section"]=$((counts["$section"] + 1))
            fi
        done
    done

    # calculate average and save results
    for section in "${sections[@]}"; do
        if [[ ${counts["$section"]} -gt 0 ]]; then
            echo "$workload $section $(for metric in "${metrics[@]}"; do echo -n "$(echo "scale=2; ${sums["$section $metric"]} / ${counts["$section"]}" | bc) "; done)" >> $result_file
        fi
    done
done


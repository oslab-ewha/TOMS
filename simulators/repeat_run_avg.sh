#!/bin/bash

# set experimental values
# workloads=(0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1.0 1.05 1.1 1.15 1.2)
workloads=(0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9 )

networkUp=100
networkDown=100
seed=0
iterations=1

tmp_dir="./tmp"

# Remove and recreate tmp directory for fresh start
if [ -d "$tmp_dir" ]; then
    echo "Removing existing tmp directory..."
    rm -rf "$tmp_dir"
fi
mkdir -p "$tmp_dir"

# set the name of the result_file
result_file="$tmp_dir/result_${networkUp}_${networkDown}_${iterations}.txt"

echo "Workload Section Power Util CPU_Power Memory_Power Network_Power Offloading_Ratio CPU_Frequency_1 CPU_Frequency_0.5 CPU_Frequency_0.25 CPU_Frequency_0.125" > $result_file

# conduct experiments according to workload
for workload in "${workloads[@]}"; do
    echo "Running workload: $workload"
    # set utilCpu
    utilCpu=$(echo "$workload - 0.01" | bc)

    # Initializing variables for calculating averages
    declare -A sums
    declare -A counts

    sections=("CO-DMO-CT" "CO-DMO" "Offloading" "DVS" "Baseline")
    metrics=("Power" "Util" "CPU_Power" "Memory_Power" "Network_Power" "Offloading_Ratio" "CPU_Frequency_1" "CPU_Frequency_0.5" "CPU_Frequency_0.25" "CPU_Frequency_0.125")

    for section in "${sections[@]}"; do
        for metric in "${metrics[@]}"; do
            sums["$section $metric"]=0
        done
        counts["$section"]=0
    done

    for ((i = 1; i <= iterations; i++)); do
        echo "Iteration $i for workload $workload..."

        # run "run.sh" and find the most recent output directory
        ./run.sh $workload $utilCpu $networkUp $networkDown $seed > /dev/null 2>&1
        latest_output_dir=$(ls -td tmp/output_${workload}+* 2>/dev/null | head -1 | sed 's/:$//')
        
        if [[ -z "$latest_output_dir" ]]; then
            echo "Warning: Could not find output directory for workload $workload iteration $i"
            continue
        fi

        # Extract values from output file
        output_file="$latest_output_dir/output_${workload}+${networkUp}.txt"
        
        if [[ ! -f "$output_file" ]]; then
            echo "Warning: Output file not found: $output_file"
            continue
        fi

        for section in "${sections[@]}"; do
            case $section in
                "CO-DMO-CT")
                    # Extract CO-DMO-CT section data
                    power=$(grep -A 10 "^\*CO-DMO-CT" "$output_file" | grep "^power:" | awk '{print $2}')
                    util=$(grep -A 10 "^\*CO-DMO-CT" "$output_file" | grep "^power:" | awk '{print $4}')
                    cpu_power=$(grep -A 10 "^\*CO-DMO-CT" "$output_file" | grep "^cpu power:" | awk '{print $3}')
                    memory_power=$(grep -A 10 "^\*CO-DMO-CT" "$output_file" | grep "^cpu power:" | awk '{print $6}')
                    network_power=$(grep -A 10 "^\*CO-DMO-CT" "$output_file" | grep "^cpu power:" | awk '{print $9}')
                    ratio=$(grep -A 10 "^\*CO-DMO-CT" "$output_file" | grep "^offloading ratio:" | awk '{print $3}')
                    freq_line=$(grep -A 10 "^\*CO-DMO-CT" "$output_file" | grep -A 2 "^cpu frequency:" | tail -1)
                    freq_1=$(echo "$freq_line" | awk '{print $1}')
                    freq_0_5=$(echo "$freq_line" | awk '{print $2}')
                    freq_0_25=$(echo "$freq_line" | awk '{print $3}')
                    freq_0_125=$(echo "$freq_line" | awk '{print $4}')
                    ;;
                "CO-DMO")
                    # Extract CO-DMO section data (not CO-DMO-CT)
                    power=$(grep -A 10 "^\*CO-DMO$" "$output_file" | grep "^power:" | awk '{print $2}')
                    util=$(grep -A 10 "^\*CO-DMO$" "$output_file" | grep "^power:" | awk '{print $4}')
                    cpu_power=$(grep -A 10 "^\*CO-DMO$" "$output_file" | grep "^cpu power:" | awk '{print $3}')
                    memory_power=$(grep -A 10 "^\*CO-DMO$" "$output_file" | grep "^cpu power:" | awk '{print $6}')
                    network_power=$(grep -A 10 "^\*CO-DMO$" "$output_file" | grep "^cpu power:" | awk '{print $9}')
                    ratio=$(grep -A 10 "^\*CO-DMO$" "$output_file" | grep "^offloading ratio:" | awk '{print $3}')
                    freq_line=$(grep -A 10 "^\*CO-DMO$" "$output_file" | grep -A 2 "^cpu frequency:" | tail -1)
                    freq_1=$(echo "$freq_line" | awk '{print $1}')
                    freq_0_5=$(echo "$freq_line" | awk '{print $2}')
                    freq_0_25=$(echo "$freq_line" | awk '{print $3}')
                    freq_0_125=$(echo "$freq_line" | awk '{print $4}')
                    ;;
                "Offloading")
                    power=$(grep -A 10 "^\*Offloading" "$output_file" | grep "^power:" | awk '{print $2}')
                    util=$(grep -A 10 "^\*Offloading" "$output_file" | grep "^power:" | awk '{print $4}')
                    cpu_power=$(grep -A 10 "^\*Offloading" "$output_file" | grep "^cpu power:" | awk '{print $3}')
                    memory_power=$(grep -A 10 "^\*Offloading" "$output_file" | grep "^cpu power:" | awk '{print $6}')
                    network_power=$(grep -A 10 "^\*Offloading" "$output_file" | grep "^cpu power:" | awk '{print $9}')
                    ratio=$(grep -A 10 "^\*Offloading" "$output_file" | grep "^offloading ratio:" | awk '{print $3}')
                    freq_line=$(grep -A 10 "^\*Offloading" "$output_file" | grep -A 2 "^cpu frequency:" | tail -1)
                    freq_1=$(echo "$freq_line" | awk '{print $1}')
                    freq_0_5=$(echo "$freq_line" | awk '{print $2}')
                    freq_0_25=$(echo "$freq_line" | awk '{print $3}')
                    freq_0_125=$(echo "$freq_line" | awk '{print $4}')
                    ;;
                "DVS")
                    power=$(grep -A 10 "^\*DVS" "$output_file" | grep "^power:" | awk '{print $2}')
                    util=$(grep -A 10 "^\*DVS" "$output_file" | grep "^power:" | awk '{print $4}')
                    cpu_power=$(grep -A 10 "^\*DVS" "$output_file" | grep "^cpu power:" | awk '{print $3}')
                    memory_power=$(grep -A 10 "^\*DVS" "$output_file" | grep "^cpu power:" | awk '{print $6}')
                    network_power=$(grep -A 10 "^\*DVS" "$output_file" | grep "^cpu power:" | awk '{print $9}')
                    ratio=$(grep -A 10 "^\*DVS" "$output_file" | grep "^offloading ratio:" | awk '{print $3}')
                    freq_line=$(grep -A 10 "^\*DVS" "$output_file" | grep -A 2 "^cpu frequency:" | tail -1)
                    freq_1=$(echo "$freq_line" | awk '{print $1}')
                    freq_0_5=$(echo "$freq_line" | awk '{print $2}')
                    freq_0_25=$(echo "$freq_line" | awk '{print $3}')
                    freq_0_125=$(echo "$freq_line" | awk '{print $4}')
                    ;;
                "Baseline")
                    power=$(grep -A 10 "^\*Baseline" "$output_file" | grep "^power:" | awk '{print $2}')
                    util=$(grep -A 10 "^\*Baseline" "$output_file" | grep "^power:" | awk '{print $4}')
                    cpu_power=$(grep -A 10 "^\*Baseline" "$output_file" | grep "^cpu power:" | awk '{print $3}')
                    memory_power=$(grep -A 10 "^\*Baseline" "$output_file" | grep "^cpu power:" | awk '{print $6}')
                    network_power=$(grep -A 10 "^\*Baseline" "$output_file" | grep "^cpu power:" | awk '{print $9}')
                    ratio=$(grep -A 10 "^\*Baseline" "$output_file" | grep "^offloading ratio:" | awk '{print $3}')
                    freq_line=$(grep -A 10 "^\*Baseline" "$output_file" | grep -A 2 "^cpu frequency:" | tail -1)
                    freq_1=$(echo "$freq_line" | awk '{print $1}')
                    freq_0_5=$(echo "$freq_line" | awk '{print $2}')
                    freq_0_25=$(echo "$freq_line" | awk '{print $3}')
                    freq_0_125=$(echo "$freq_line" | awk '{print $4}')
                    ;;
            esac

            # calculate sum of values - with validation
            if [[ -n "$power" && "$power" != "" && "$power" =~ ^[0-9]*\.?[0-9]+$ ]]; then
                sums["$section Power"]=$(echo "scale=6; ${sums["$section Power"]} + $power" | bc -l)
                if [[ -n "$util" && "$util" =~ ^[0-9]*\.?[0-9]+$ ]]; then
                    sums["$section Util"]=$(echo "scale=6; ${sums["$section Util"]} + $util" | bc -l)
                fi
                if [[ -n "$cpu_power" && "$cpu_power" =~ ^[0-9]*\.?[0-9]+$ ]]; then
                    sums["$section CPU_Power"]=$(echo "scale=6; ${sums["$section CPU_Power"]} + $cpu_power" | bc -l)
                fi
                if [[ -n "$memory_power" && "$memory_power" =~ ^[0-9]*\.?[0-9]+$ ]]; then
                    sums["$section Memory_Power"]=$(echo "scale=6; ${sums["$section Memory_Power"]} + $memory_power" | bc -l)
                fi
                if [[ -n "$network_power" && "$network_power" =~ ^[0-9]*\.?[0-9]+$ ]]; then
                    sums["$section Network_Power"]=$(echo "scale=6; ${sums["$section Network_Power"]} + $network_power" | bc -l)
                fi
                if [[ -n "$ratio" && "$ratio" =~ ^[0-9]*\.?[0-9]+$ ]]; then
                    sums["$section Offloading_Ratio"]=$(echo "scale=6; ${sums["$section Offloading_Ratio"]} + $ratio" | bc -l)
                fi
                if [[ -n "$freq_1" && "$freq_1" =~ ^[0-9]+$ ]]; then
                    sums["$section CPU_Frequency_1"]=$(echo "scale=6; ${sums["$section CPU_Frequency_1"]} + $freq_1" | bc -l)
                fi
                if [[ -n "$freq_0_5" && "$freq_0_5" =~ ^[0-9]+$ ]]; then
                    sums["$section CPU_Frequency_0.5"]=$(echo "scale=6; ${sums["$section CPU_Frequency_0.5"]} + $freq_0_5" | bc -l)
                fi
                if [[ -n "$freq_0_25" && "$freq_0_25" =~ ^[0-9]+$ ]]; then
                    sums["$section CPU_Frequency_0.25"]=$(echo "scale=6; ${sums["$section CPU_Frequency_0.25"]} + $freq_0_25" | bc -l)
                fi
                if [[ -n "$freq_0_125" && "$freq_0_125" =~ ^[0-9]+$ ]]; then
                    sums["$section CPU_Frequency_0.125"]=$(echo "scale=6; ${sums["$section CPU_Frequency_0.125"]} + $freq_0_125" | bc -l)
                fi
                counts["$section"]=$((counts["$section"] + 1))
            fi
        done
    done

    # calculate average and save results
    for section in "${sections[@]}"; do
        if [[ ${counts["$section"]} -gt 0 ]]; then
            echo "$workload $section $(for metric in "${metrics[@]}"; do echo -n "$(echo "scale=2; ${sums["$section $metric"]} / ${counts["$section"]}" | bc -l) "; done)" >> $result_file
        fi
    done
done


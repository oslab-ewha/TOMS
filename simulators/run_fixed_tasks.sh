#!/bin/bash

# Create output directories
OUTPUT=./tmp/output_fixed+$$
mkdir -p $OUTPUT
mkdir -p $OUTPUT/conf
mkdir -p $OUTPUT/report
mkdir -p $OUTPUT/task
touch $OUTPUT/output_fixed.txt

# Function to run simulation with different configurations
run_simulation() {
    local algo=$1
    local conf_file="$OUTPUT/conf/gastask_${algo}_fixed+$$.conf"
    
    # Copy base configuration
    cp gastask_candy.conf "$conf_file"
    
    # Modify configuration based on algorithm
    case $algo in
        "CO-DMO-CT")
            # TEE=1, All optimizations enabled
            # Already has all optimizations enabled by default
            ;;
        "CO-DMO")
            # TEE=0, All optimizations enabled
            sed -i 's/*TEE\n1/*TEE\n0/' "$conf_file"
            ;;
        "Offloading")
            # TEE=0, Only offloading
            sed -i 's/*TEE\n1/*TEE\n0/' "$conf_file"
            # Remove DVFS options except the base frequency
            sed -i '/*cpufreq/,/^$/c\# wcet_scale power_active power_idle\n*cpufreq\n1    100    1' "$conf_file"
            # Remove NVRAM option, only DRAM
            sed -i '/*mem/,/^$/c\# type max_capacity wcet_scale power_active power_idle\n*mem\ndram  1000 1    0.01   0.009' "$conf_file"
            ;;
        "DVS")
            # TEE=0, Only DVFS
            sed -i 's/*TEE\n1/*TEE\n0/' "$conf_file"
            # Disable offloading
            sed -i 's/*offloadingratio\n0\n1/*offloadingratio\n0/' "$conf_file"
            sed -i 's/\t1$/\t0/g' "$conf_file"  # Set all tasks to local execution
            # Remove NVRAM option, only DRAM
            sed -i '/*mem/,/^$/c\# type max_capacity wcet_scale power_active power_idle\n*mem\ndram  1000 1    0.01   0.009' "$conf_file"
            ;;
        "Baseline")
            # TEE=0, No optimizations
            sed -i 's/*TEE\n1/*TEE\n0/' "$conf_file"
            # Remove DVFS options except base frequency
            sed -i '/*cpufreq/,/^$/c\# wcet_scale power_active power_idle\n*cpufreq\n1    100    1' "$conf_file"
            # Disable offloading
            sed -i 's/*offloadingratio\n0\n1/*offloadingratio\n0/' "$conf_file"
            sed -i 's/\t1$/\t0/g' "$conf_file"  # Set all tasks to local execution
            ;;
        *)
            echo "Unknown algorithm: $algo"
            return 1
            ;;
    esac
    
    # Run simulation
    echo "*$algo" >> $OUTPUT/output_fixed.txt
    ./gastask $conf_file | tee -a $OUTPUT/output_fixed.txt
    mv task.txt $OUTPUT/task/task_fixed_${algo}.txt
    mv report.txt $OUTPUT/report/report_fixed_${algo}.txt 2>/dev/null || true
    echo "" >> $OUTPUT/output_fixed.txt
}

# Run all algorithms
echo "Running simulations..."

# 1. CO-DMO-CT (TEE=1, All optimizations enabled)
run_simulation "CO-DMO-CT"

# 2. CO-DMO (TEE=0, All optimizations enabled)
run_simulation "CO-DMO"

# 3. Offloading (TEE=0, Only offloading)
run_simulation "Offloading"

# 4. DVS (TEE=0, Only DVFS)
run_simulation "DVS"

# 5. Baseline (TEE=0, No optimizations)
run_simulation "Baseline"

echo "Simulation completed. Results saved in $OUTPUT"

#!/bin/bash

# Clean up previous results
rm -rf ./tmp

# Create directories for results
mkdir -p ./tmp/result_network/details

# Add header to combined results file
echo "Network Section Power Util CPU_Power Memory_Power Network_Power Offloading_Ratio CPU_Frequency_1 CPU_Frequency_0.5 CPU_Frequency_0.25 CPU_Frequency_0.125" > ./tmp/result_network/combined_results.txt

# Make sure gastask is executable
chmod +x ./gastask

# Run simulations for each bandwidth
for bw in {10..100..10}; do
  echo "Running simulation for bandwidth ${bw}..."
  ./run_iot_tasks.sh ${bw} 1
done

echo "All simulations completed. Results are in ./tmp/result_network/"

import os
import sys
import shutil
import subprocess
from pathlib import Path


# def usage():
#     print("Usage: run_batch.py <util_target> <util_cpu> <network_up> <network_down> <seed>")


util_target = 0.8
util_cpu = 0.7
network_up = 100
network_down = 100
seed = 0

pid = str(os.getpid())
base_name = f"{util_target}+{pid}"

conf_dir = Path("./tmp")
conf_dir.mkdir(exist_ok=True)
gastask_conf = conf_dir / f"gastask_{base_name}.conf"
output_dir = conf_dir / f"output_{base_name}"
output_dir.mkdir(exist_ok=True)

common_conf = f"""\
# max_generations n_populations cutoff penalty
*genetic
10000 100 1.5 1.5

# wcet_min wcet_max mem_total util_cpu util_target n_tasks task_size_min task_size_max input_size_min input_size_max output_size_min output_size_max
*gentask
500 1000 2000 {util_cpu} {util_target} 100 4000 6000 800 4000 800 2000

# uplink_min uplink_max downlink_min downlink_max n_networks
*gennetwork
{network_up} {network_up} {network_down} {network_down} 100

# intercept_out_min intercept_out_max intercept_in_min intercept_in_max n_net_commanders
*gennetcommander
1 5 5 7 100

# wcet_scale power_active power_idle
*cpufreq
1    100    1
0.5  25   0.25
0.25 6.25 0.0625
0.125 1.5625 0.015625

# type max_capacity wcet_scale power_active power_idle
*mem
dram  1000 1    0.01   0.01
nvram 1000 0.8  0.01   0.0001

# type computation_power power_active power_idle max_capacity offloading_limit
*cloud
mec  2   400   100   100000   1.0

# offloading_ratio 
*offloadingratio
0
1

# TEE 
*TEE
0
#1

# uplink_data_rate downlink_data_rate
*network
"""

with open(gastask_conf, "w") as f:
    f.write(common_conf)

subprocess.run(["./gasgen", str(gastask_conf)])
with open("network_generated.txt") as src, open(gastask_conf, "a") as dst:
    dst.write(src.read())

with open(gastask_conf, "a") as f:
    f.write("\n# intercept_out intercept_in\n*netcommander\n")
with open("network_commander_generated.txt") as src, open(gastask_conf, "a") as dst:
    dst.write(src.read())

with open(gastask_conf, "a") as f:
    f.write("\n# wcet period memreq mem_active_ratio input_data_size output_data_size\n*task\n")
with open("task_generated.txt") as src, open(gastask_conf, "a") as dst:
    dst.write(src.read())

shutil.move("task_generated.txt", output_dir / f"gen_task_generated_{base_name}.txt")
shutil.move("network_commander_generated.txt", output_dir / f"gen_network_commander_generated_{base_name}.txt")

output_file = output_dir / f"output_{util_target}+{network_up}.txt"

def sed_replace(filename, line_num, old, new):
    with open(filename, "r") as f:
        lines = f.readlines()
    if line_num < len(lines):
        lines[line_num] = lines[line_num].replace(old, new)
    with open(filename, "w") as f:
        f.writelines(lines)

modes = [
    ("CO-DMO-DT", [(19, "0", "#0"), (20, "#1", "1"), (21, "0.5", "#0.5"), (22, "0.25", "#0.25"), (23, "0.125", "#0.125")]),
    ("CO-DMO", []),
    ("Offloading", [(21, "0.5", "#0.5"), (22, "0.25", "#0.25"), (23, "0.125", "#0.125")]),
    ("DVS", [(37, "1", "#1")]),
    ("Baseline", [(21, "0.5", "#0.5"), (22, "0.25", "#0.25"), (23, "0.125", "#0.125")])
    ]

for mode, sed_ops in modes:
    with open(output_file, "a") as f:
        f.write(f"\n*{mode}\n")
    subprocess.run(["./gastask", "-s", str(seed), str(gastask_conf)], stdout=open(output_file, "a"))
    shutil.move("task.txt", output_dir / f"task_{util_target}+{network_up}+{mode}.txt")
    for line, before, after in sed_ops:
        sed_replace(gastask_conf, line, before, after)

restore_lines = [
    (19, "#0", "0"),
    (20, "1", "#1"),
    (21, "#0.5", "0.5"),
    (22, "#0.25", "0.25"),
    (23, "#0.125", "0.125")
]
for line, before, after in restore_lines:
    sed_replace(gastask_conf, line, before, after)

shutil.move(gastask_conf, output_dir / gastask_conf.name)

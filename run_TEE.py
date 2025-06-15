import os
import shutil
import subprocess
from pathlib import Path
import uuid

# ✅ 환경변수에서 실험 파라미터 받아오기
util_target = float(os.environ.get("UTIL_TARGET", 0.5))
util_cpu = float(os.environ.get("UTIL_CPU", 0.4))
network_up = int(os.environ.get("NETWORK_UP", 100))
network_down = int(os.environ.get("NETWORK_DOWN", 120))
seed = int(os.environ.get("SEED", 0))

# ✅ 고유한 이름을 위한 식별자
pid = str(uuid.uuid4().hex[:8])
base_name = f"{util_target}+{pid}"

# ✅ 디렉토리 설정
conf_dir = Path("./tmp")
conf_dir.mkdir(exist_ok=True)
gastask_conf = conf_dir / f"gastask_{base_name}.conf"
output_dir = conf_dir / f"output_{base_name}"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / f"output_{util_target}+{network_up}.txt"

# ✅ 공통 설정 파일 작성
common_conf = f"""# max_generations n_populations cutoff penalty
*genetic
10000 100 1.5 1.5

*gentask
500 1000 2000 {util_cpu} {util_target} 100 4000 6000 800 4000 800 2000

*gennetwork
{network_up} {network_up} {network_down} {network_down} 100

*gennetcommander
1 5 5 7 100

*cpufreq
1    100    1
0.5  25   0.25
0.25 6.25 0.0625
0.125 1.5625 0.015625

*mem
dram  1000 1    0.01   0.01
nvram 1000 0.8  0.01   0.0001

*cloud
mec  2   400   100   100000   1.0

*offloadingratio
0
1

*TEE
0
#1

*network
"""

with open(gastask_conf, "w") as f:
    f.write(common_conf)

# ✅ 데이터 생성
subprocess.run(["./gasgen", str(gastask_conf)], check=True)

with open("network_generated.txt") as src, open(gastask_conf, "a") as dst:
    dst.write(src.read())

with open(gastask_conf, "a") as f:
    f.write("\n*netcommander\n")
with open("network_commander_generated.txt") as src, open(gastask_conf, "a") as dst:
    dst.write(src.read())

with open(gastask_conf, "a") as f:
    f.write("\n*task\n")
with open("task_generated.txt") as src, open(gastask_conf, "a") as dst:
    dst.write(src.read())

shutil.move("task_generated.txt", output_dir / f"gen_task_generated_{base_name}.txt")
shutil.move("network_commander_generated.txt", output_dir / f"gen_network_commander_generated_{base_name}.txt")

# ✅ 설정 줄 바꾸기 함수
def sed_replace(filename, line_num, old, new):
    with open(filename, "r") as f:
        lines = f.readlines()
    if line_num < len(lines):
        lines[line_num] = lines[line_num].replace(old, new)
    with open(filename, "w") as f:
        f.writelines(lines)

# ✅ 실험 모드 구성
modes = [
    ("CO-DMO-DT", [(19, "0", "#0"), (20, "#1", "1"),
                   (21, "0.5", "#0.5"), (22, "0.25", "#0.25"), (23, "0.125", "#0.125")]),
    ("CO-DMO", []),
    ("Offloading", [(21, "0.5", "#0.5"), (22, "0.25", "#0.25"), (23, "0.125", "#0.125")]),
    ("DVS", [(37, "1", "#1")]),
    ("Baseline", [(21, "0.5", "#0.5"), (22, "0.25", "#0.25"), (23, "0.125", "#0.125")])
]

# ✅ 각 모드 실행
for mode, sed_ops in modes:
    with open(output_file, "a") as f:
        f.write(f"\n*{mode}\n")

    # CO-DMO-DT 이후 TEE 정확히 복원
    if mode == "CO-DMO":
        sed_replace(gastask_conf, 19, "#0", "0")    # 19번 줄 다시 0
        sed_replace(gastask_conf, 20, "1", "#1")    # 20번 줄 다시 주석처리
        sed_replace(gastask_conf, 19, "1", "0")     # 혹시 1이 남아있을 경우도 방지

    subprocess.run(["./gastask", "-s", str(seed), str(gastask_conf)],
                   stdout=open(output_file, "a"))

    shutil.move("task.txt", output_dir / f"task_{util_target}+{network_up}+{mode}.txt")

    for line, before, after in sed_ops:
        sed_replace(gastask_conf, line, before, after)

# ✅ 설정 원복
restore_lines = [
    (19, "#0", "0"),
    (20, "1", "#1"),
    (21, "#0.5", "0.5"),
    (22, "#0.25", "0.25"),
    (23, "#0.125", "0.125"),
    (37, "#1", "1")
]
for line, before, after in restore_lines:
    sed_replace(gastask_conf, line, before, after)

shutil.move(gastask_conf, output_dir / gastask_conf.name)

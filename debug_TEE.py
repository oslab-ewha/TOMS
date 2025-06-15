import os
import shutil
import subprocess
from pathlib import Path
import uuid

# ✅ 환경 변수
util_target = float(os.environ.get("UTIL_TARGET", 0.5))
util_cpu = float(os.environ.get("UTIL_CPU", 0.4))
network_up = int(os.environ.get("NETWORK_UP", 100))
network_down = int(os.environ.get("NETWORK_DOWN", 120))
seed = int(os.environ.get("SEED", 0))

# ✅ 고유 이름 및 디렉토리 구성
pid = str(uuid.uuid4().hex[:8])
base_name = f"{util_target}+{pid}"
conf_dir = Path("./tmp")
conf_dir.mkdir(exist_ok=True)
output_dir = conf_dir / f"output_{base_name}"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / f"output_{util_target}+{network_up}.txt"

# ✅ 공통 설정 문자열
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

# ✅ conf 파일 작성 함수
def write_conf(name, extra_lines):
    path = conf_dir / name
    with open(path, "w") as f:
        f.write(common_conf)
        for fname, header in [
            ("network_generated.txt", ""),
            ("network_commander_generated.txt", "\n*netcommander\n"),
            ("task_generated.txt", "\n*task\n"),
        ]:
            if Path(fname).exists():
                f.write(header)
                with open(fname) as src:
                    f.write(src.read())
        f.writelines(extra_lines)
    return path

# ✅ 하드코딩된 각 모드의 추가 설정
confs = {
    "CO-DMO-DT": write_conf("comm1.conf", [
        "#0\n", "1\n"
    ]),
    "CO-DMO": write_conf("comm2.conf", [
        "0\n", "#1\n"
    ]),
    "Offloading": write_conf("comm3.conf", [
        "#0.5  25   0.25\n",
        "#0.25 6.25 0.0625\n",
        "#0.125 1.5625 0.015625\n"
    ]),
    "DVS": write_conf("comm4.conf", [
        "#0\n", "#1\n"
    ]),
    "Baseline": write_conf("comm5.conf", [
        "#0.5  25   0.25\n",
        "#0.25 6.25 0.0625\n",
        "#0.125 1.5625 0.015625\n",
        "#0\n", "#1\n"
    ]),
}

# ✅ 원본 생성 파일들도 output_dir에 보관
for f in ["task_generated.txt", "network_commander_generated.txt"]:
    if Path(f).exists():
        shutil.move(f, output_dir / f"gen_{f}")

# ✅ 모드 실행 루프
for mode, conf_path in confs.items():
    print(f"\n==== Running Mode: {mode} ====")
    with open(output_file, "a") as f:
        f.write(f"\n*{mode}\n")
    try:
        subprocess.run(["./gastask", "-s", str(seed), str(conf_path)],
                       check=True, stdout=f)
        if Path("task.txt").exists():
            shutil.move("task.txt", output_dir / f"task_{util_target}+{network_up}+{mode}.txt")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] gastask failed in mode {mode}: {e}")

    shutil.copy(conf_path, output_dir / conf_path.name)

print("\n✅ All modes completed.")

#!/usr/bin/env python3
import os, shutil, subprocess, sys, re
from pathlib import Path

BASE_CONF = Path("candy_cycle.conf")
OUTPUT_ROOT = Path("./tmp")

SCENARIOS = [
    ("CO-DMO-DT", 1, True,  True),
    ("CO-DMO",    0, True,  True),
    ("Offloading",0, True,  False),
    ("DVS",       0, False, True),
    ("Baseline",  0, False, False),
]

def modify_config_direct(base_path, out_path, tee_enabled, offloading_enabled, dvfs_enabled, algorithm_name):
    """직접 config 파일을 수정"""
    with open(base_path, 'r') as f:
        lines = f.readlines()

    # TEE 설정
    for i, line in enumerate(lines):
        if line.strip().startswith('*TEE'):
            if i + 1 < len(lines):
                lines[i + 1] = f"{tee_enabled}\n"
                break

    # 메모리 설정 (CO-DMO가 아니면 dram만 남기고 nvram은 주석처리)
    if not str(algorithm_name).startswith('CO-DMO'):
        in_mem = False
        for i, line in enumerate(lines):
            if line.strip().startswith('*mem'):
                in_mem = True
                continue
            if in_mem and (line.strip() == '' or line.startswith('*')):
                in_mem = False
            if in_mem and not line.strip().startswith('#'):
                # nvram 라인을 주석처리
                if 'nvram' in line.lower():
                    lines[i] = '#' + line

    # DVFS 설정 (비활성화시 첫번째 주파수만 남기고 나머지는 주석처리)
    if not dvfs_enabled:
        in_cpufreq = False
        first_freq_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('*cpufreq'):
                in_cpufreq = True
                continue
            if in_cpufreq and (line.strip() == '' or line.startswith('*')):
                in_cpufreq = False
            if in_cpufreq and not line.strip().startswith('#'):
                # 첫 번째 주파수 라인이 아니면 주석처리
                if re.match(r'^\s*[0-9.]+\s+', line):
                    if first_freq_found:
                        lines[i] = '#' + line
                    else:
                        first_freq_found = True

    # 오프로딩 설정 (비활성화시 offloadingratio를 0으로, "1"은 주석처리)
    if not offloading_enabled:
        in_off = False
        for i, line in enumerate(lines):
            if line.strip().startswith('*offloadingratio'):
                in_off = True
                continue
            if in_off and (line.strip() == '' or line.startswith('*')):
                in_off = False
            if in_off and not line.strip().startswith('#'):
                if line.strip() == '1':
                    lines[i] = '#1\n'

        # 모든 task를 local로
        in_task = False
        for i, line in enumerate(lines):
            if line.strip().startswith('*task'):
                in_task = True
                continue
            if in_task and (line.strip() == '' or line.startswith('*')):
                in_task = False
            if in_task and re.match(r'^\d', line.strip()):
                parts = line.strip().split()
                if parts:
                    parts[-1] = '0'
                    lines[i] = ' '.join(parts) + '\n'

    with open(out_path, 'w') as f:
        f.writelines(lines)

def run_experiment(util_target, util_cpu, network_up, network_down, seed):
    pid = os.getpid()
    outdir = OUTPUT_ROOT / f"output_{util_target}+{pid}"
    (outdir / "conf").mkdir(parents=True, exist_ok=True)
    (outdir / "report").mkdir(exist_ok=True)
    (outdir / "task").mkdir(exist_ok=True)

    main_out = outdir / f"output_{util_target}+{network_up}.txt"
    main_out.write_text("", encoding="utf-8")

    for name, tee, offl, dvfs in SCENARIOS:
        print(f"Running {name}...")
        conf_path = outdir / "conf" / f"gastask_{name}_{util_target}+{pid}.conf"

        # 1) 직접 config 생성
        modify_config_direct(BASE_CONF, conf_path, tee, offl, dvfs, name)

        # 2) gastask 실행
        with open(main_out, "a", encoding="utf-8") as f:
            f.write(f"*{name}\n")
        proc = subprocess.run(
            ["./gastask", "-s", str(seed), str(conf_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        with open(main_out, "a", encoding="utf-8") as f:
            f.write(proc.stdout)

        # 3) 산출물 이동
        for filename, sub in [("task.txt","task"), ("report.txt","report")]:
            src = Path(filename)
            if src.exists():
                dst = outdir / sub / f"{sub}_{util_target}+{network_up}+{name}.txt"
                shutil.move(src, dst)

    print(f"Simulation completed. Results saved in {outdir}")

if __name__ == "__main__":
    # 간단한 network 매개변수만 받기
    if len(sys.argv) < 2:
        network_bandwidth = 120  # 기본값
    else:
        network_bandwidth = int(sys.argv[1])
    
    # 기본 매개변수로 실험 실행
    util = "0.8"
    util_cpu = "0.8" 
    net_up = str(network_bandwidth)
    net_down = str(network_bandwidth)
    seed = "0"

    run_experiment(util, util_cpu, net_up, net_down, seed)

import os
import subprocess
from decimal import Decimal
from pathlib import Path

# 실험 파라미터
workloads = [round(x * 0.05, 2) for x in range(1, 25)]  # 0.05 ~ 1.2
network_up = 120
network_down = 120
seed = 0
iterations = 3

output_dir = Path("./tmp")
output_dir.mkdir(exist_ok=True)
result_file = output_dir / f"result_{network_up}_{network_down}_{iterations}.txt"

sections = ["CO-DMO-DT", "CO-DMO", "Offloading", "DVS", "Baseline"]
metrics = ["Power", "Util", "CPU_Power", "Memory_Power", "Network_Power",
           "Offloading_Ratio", "CPU_Frequency_1", "CPU_Frequency_0.5",
           "CPU_Frequency_0.25", "CPU_Frequency_0.125"]

def safe_decimal(val):
    try:
        return Decimal(val)
    except:
        return Decimal("0.0")

# 결과 헤더 작성
with open(result_file, "w") as f:
    f.write("Workload Section " + " ".join(metrics) + "\n")

# 반복 실행
for workload in workloads:
    util_cpu = round(workload - 0.025, 3)
    print(f"\n🔁 Workload: {workload} | Util_CPU: {util_cpu}")

    sums = {f"{section} {metric}": Decimal("0.0") for section in sections for metric in metrics}
    counts = {section: 0 for section in sections}

    for i in range(iterations):
        print(f"   ▶ Iteration {i+1}")
        env = os.environ.copy()
        env.update({
            "UTIL_TARGET": str(workload),
            "UTIL_CPU": str(util_cpu),
            "NETWORK_UP": str(network_up),
            "NETWORK_DOWN": str(network_down),
            "SEED": str(seed)
        })

        try:
            subprocess.run(["python3", "run_TEE_updated.py"], env=env, check=True, timeout=300)
        except Exception as e:
            print(f"   ⚠️ 실행 실패: {e}")
            continue

        # 최신 output 파일 확인
        output_files = sorted(output_dir.glob(f"output_{workload}*.txt"), reverse=True)
        if not output_files:
            print("   ⚠️ 출력 파일 없음")
            continue

        output_file = output_files[0]
        with open(output_file) as f:
            lines = f.readlines()

        for section in sections:
            try:
                base = next(i for i, line in enumerate(lines) if line.strip() == f"*{section}")
                power = safe_decimal(lines[base + 2].split()[1])
                util = safe_decimal(lines[base + 2].split()[3])
                cpu_power = safe_decimal(lines[base + 3].split()[2])
                memory_power = safe_decimal(lines[base + 3].split()[5])
                network_power = safe_decimal(lines[base + 3].split()[8])
                ratio = safe_decimal(lines[base + 4].split()[2])
                freqs = list(map(safe_decimal, lines[base + 7].split()[:4]))

                values = [power, util, cpu_power, memory_power, network_power, ratio] + freqs
                for metric, value in zip(metrics, values):
                    sums[f"{section} {metric}"] += value
                counts[section] += 1

            except Exception as e:
                print(f"   ⚠️ 파싱 실패 - {section} @ workload={workload}: {e}")

    # 평균 결과 저장
    with open(result_file, "a") as f:
        for section in sections:
            if counts[section] > 0:
                averages = [round(sums[f"{section} {metric}"] / counts[section], 2) for metric in metrics]
                f.write(f"{workload} {section} {' '.join(map(str, averages))}\n")

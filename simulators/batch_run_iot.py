import os
import re
import csv
import subprocess
from collections import defaultdict

# 현재 스크립트 위치로 이동
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 설정
run_script = "./run_iot.sh"
tmp_dir = "./tmp"
network_values = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120]  # Mbps
repeat = 3   # 🔹 네트워크당 반복 실행 횟수
seed = 42    # 고정 시드

# 1️⃣ 배치 실행 (반복 기능 추가)
for net in network_values:
    for r in range(repeat):
        print(f"▶ Running simulation for network {net} Mbps... (Run {r+1}/{repeat})")
        subprocess.run([run_script, str(net), str(net), str(seed)], check=True)

# 2️⃣ 결과 파싱
result_csv = os.path.join(tmp_dir, "network_results.csv")

def parse_section(lines):
    data = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("power:"):
            parts = line.split()
            if len(parts) >= 4:
                data["Power"] = float(parts[1])
                data["Util"] = float(parts[3])
        elif line.startswith("cpu power:"):
            parts = line.split()
            if len(parts) >= 9:
                data["CPU_Power"] = float(parts[2])
                data["Memory_Power"] = float(parts[5])
                data["Network_Power"] = float(parts[8])
        elif line.startswith("offloading ratio:"):
            parts = line.split()
            if len(parts) >= 3:
                data["Offloading_Ratio"] = float(parts[2])
        elif line.startswith("cpu frequency:"):
            freq_line = None
            for j in range(i+2, len(lines)):
                if lines[j].strip():
                    freq_line = lines[j]
                    break
            if freq_line:
                freq_values = freq_line.split()
                if len(freq_values) >= 4:
                    data["CPU_Frequency_1"] = int(freq_values[0])
                    data["CPU_Frequency_0.5"] = int(freq_values[1])
                    data["CPU_Frequency_0.25"] = int(freq_values[2])
                    data["CPU_Frequency_0.125"] = int(freq_values[3])
        i += 1
    return data

sums = defaultdict(lambda: defaultdict(float))
counts = defaultdict(int)

sections = ["CO-DMO-CT", "CO-DMO", "Offloading", "DVS", "Baseline"]
metrics = [
    "Power", "Util", "CPU_Power", "Memory_Power", "Network_Power",
    "Offloading_Ratio", "CPU_Frequency_1", "CPU_Frequency_0.5",
    "CPU_Frequency_0.25", "CPU_Frequency_0.125"
]

for folder in os.listdir(tmp_dir):
    if folder.startswith("output_"):
        output_file = os.path.join(tmp_dir, folder, "output.txt")
        if not os.path.isfile(output_file):
            continue

        # network 값 가져오기
        gen_net_file = os.path.join(tmp_dir, folder, "gen", "gen_network_generated.txt")
        if os.path.isfile(gen_net_file):
            with open(gen_net_file) as f:
                first_line = f.readline().strip()
                try:
                    net_val = int(first_line.split()[0])
                except Exception:
                    print(f"[경고] {gen_net_file}에서 network 값 파싱 실패: '{first_line}'")
                    net_val = -1
        else:
            print(f"[경고] {gen_net_file} 없음. network=-1로 저장")
            net_val = -1

        with open(output_file, "r") as f:
            content = f.read().splitlines()

        for section in sections:
            try:
                start_idx = content.index(f"*{section}")
            except ValueError:
                print(f"[경고] section {section} not found in {output_file}")
                continue
            end_idx = len(content)
            for next_sec in sections:
                if next_sec == section:
                    continue
                try:
                    idx = content.index(f"*{next_sec}", start_idx+1)
                    if idx < end_idx:
                        end_idx = idx
                except ValueError:
                    pass
            sec_lines = content[start_idx+1:end_idx]
            parsed = parse_section(sec_lines)
            if not parsed:
                print(f"[경고] section {section} 파싱 실패 in {output_file}")
            for m in metrics:
                if m in parsed:
                    sums[(net_val, section)][m] += parsed[m]
            counts[(net_val, section)] += 1

# 섹션 순서 유지 위해 딕셔너리
section_order = {sec: i for i, sec in enumerate(sections)}

with open(result_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Network", "Section", "Count"] + metrics)

    # 네트워크 오름차순, 섹션은 sections 순서대로 정렬
    for (net_val, section), count in sorted(counts.items(), key=lambda x: (x[0][0], section_order.get(x[0][1], 999))):
        avg_vals = [sums[(net_val, section)][m] / count for m in metrics]
        writer.writerow([net_val, section, count] + avg_vals)

print(f"✅ 네트워크별 평균 결과 저장 완료: {result_csv}")

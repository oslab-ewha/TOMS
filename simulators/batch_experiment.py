#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CandyBox 배치 실험 자동화 스크립트
- Server_Power, Network, Workload, Algorithm별 실험 수행
- 결과를 체계적으로 수집하여 CSV 저장
"""

import subprocess
import re
import shutil
import csv
import os
from pathlib import Path
from itertools import product
import time

# 스크립트 위치를 기준으로 작업 디렉토리 설정
SCRIPT_DIR = Path(__file__).parent.absolute()
SIMULATORS_DIR = SCRIPT_DIR if SCRIPT_DIR.name == "simulators" else SCRIPT_DIR / "simulators"

# 작업 디렉토리를 simulators로 변경
os.chdir(SIMULATORS_DIR)
print(f"작업 디렉토리: {SIMULATORS_DIR}")

# 실험 매개변수 정의
EXPERIMENTS = {
    "server_power": [4],           # cloud computation_power
    #"server_power": [2, 4],
    "network": [10, 100],     # network bandwidth
    #"network": [10, 30, 60, 90, 120],
    #"workload": [0.2, 0.3, 0.5, 0.7, 0.9, 1.2]
    "workload": [0.7],   # TARGET_UTIL 범위
}

ALGORITHMS = ["CO-DMO-CT", "CO-DMO", "Offloading", "DVS", "Baseline"]

# 결과 저장 파일
RESULTS_FILE = Path("experiment_results.csv")
BACKUP_DIR = Path("experiment_backup")

class ExperimentRunner:
    def __init__(self):
        self.results = []
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        
    def modify_server_power(self, power):
        """cloud computation_power 수정"""
        config_file = Path("candy_cycle.conf")
        with open(config_file, 'r') as f:
            content = f.read()
        
        # *cloud 섹션의 computation_power 수정
        pattern = r'(\*cloud\nmec\s+)\d+(\s+400\s+100\s+100000\s+1\.0)'
        replacement = rf'\g<1>{power}\g<2>'
        content = re.sub(pattern, replacement, content)
        
        with open(config_file, 'w') as f:
            f.write(content)
        print(f"  Server power 설정: {power}")
    
    def modify_workload(self, target_util):
        """task_gen.py TARGET_UTIL 수정 및 태스크 재생성"""
        # task_gen.py는 simulators 폴더에 있음
        task_gen_file = Path("task_gen.py")
        
        if not task_gen_file.exists():
            print(f"  오류: {task_gen_file} 파일을 찾을 수 없습니다.")
            return
            
        print(f"  task_gen.py 수정 중: {task_gen_file.absolute()}")
            
        with open(task_gen_file, 'r') as f:
            content = f.read()
        
        # TARGET_UTIL_MIN, MAX 수정 (±0.05 범위)
        util_min = max(0.1, target_util - 0.05)
        util_max = min(1.0, target_util + 0.05)
        
        print(f"  TARGET_UTIL 범위: {util_min:.2f} ~ {util_max:.2f}")
        
        # 정규표현식으로 수정
        old_content = content
        content = re.sub(r'TARGET_UTIL_MIN = [\d.]+', f'TARGET_UTIL_MIN = {util_min}', content)
        content = re.sub(r'TARGET_UTIL_MAX = [\d.]+', f'TARGET_UTIL_MAX = {util_max}', content)
        
        # 수정 확인
        if content == old_content:
            print(f"  경고: TARGET_UTIL 값이 수정되지 않았습니다.")
        
        with open(task_gen_file, 'w') as f:
            f.write(content)
        
        # 태스크 생성
        print(f"  새 태스크 생성 중...")
        result = subprocess.run(['python', 'task_gen.py'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  태스크 생성 오류: {result.stderr}")
            return
        
        print(f"  태스크 생성 완료")
        
        # candy_cycle.conf의 *task 섹션 업데이트
        self.update_task_section()
        print(f"  Workload 설정 완료: {target_util:.1f}")
    
    def update_task_section(self):
        """task_gen.txt를 candy_cycle.conf에 반영"""
        # task_gen.txt는 현재 디렉토리에 생성됨
        task_gen_txt = Path("task_gen.txt")
        config_file = Path("candy_cycle.conf")
        
        if not task_gen_txt.exists():
            print(f"  경고: {task_gen_txt} 파일을 찾을 수 없습니다.")
            return
            
        print(f"  task_gen.txt에서 태스크 읽는 중...")
        
        # task_gen.txt에서 태스크 데이터 읽기
        with open(task_gen_txt, 'r') as f:
            lines = f.readlines()
        
        task_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        print(f"  읽은 태스크 개수: {len(task_lines)}")
        
        # candy_cycle.conf 업데이트
        with open(config_file, 'r') as f:
            content = f.read()
        
        # *task 섹션 찾아서 교체
        task_section = "# wcet period memreq mem_active_ratio task_size input_size output_size offloading_bool\n*task\n"
        task_section += '\n'.join(task_lines)
        
        # 기존 *task 섹션 교체
        old_content = content
        pattern = r'# wcet period memreq.*?\*task\n.*?(?=\n\*|\Z)'
        content = re.sub(pattern, task_section, content, flags=re.DOTALL)
        
        if content == old_content:
            print(f"  경고: candy_cycle.conf의 *task 섹션이 수정되지 않았습니다.")
        else:
            print(f"  candy_cycle.conf *task 섹션 업데이트 완료")
        
        with open(config_file, 'w') as f:
            f.write(content)
    
    def run_experiment(self, server_power, network, workload):
        """단일 실험 수행"""
        print(f"\n실험: Server={server_power}, Network={network}, Workload={workload:.1f}")
        
        # 매개변수 설정
        self.modify_server_power(server_power)
        self.modify_workload(workload)
        
        # run_candy.py 실행 (network, workload 매개변수 포함)
        cmd = ['python', 'run_candy.py', str(network), str(workload)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  실험 실패: {result.stderr}")
            return None
        
        # 결과 파싱
        return self.parse_results(server_power, network, workload)
    
    def parse_results(self, server_power, network, workload):
        """tmp/ 디렉토리에서 최신 결과 파싱"""
        tmp_dir = Path("tmp")
        if not tmp_dir.exists():
            return None
            
        # 가장 최근 결과 디렉토리 찾기
        result_dirs = [d for d in tmp_dir.iterdir() if d.is_dir() and d.name.startswith("output_")]
        if not result_dirs:
            return None
            
        latest_dir = max(result_dirs, key=lambda x: x.stat().st_mtime)
        output_files = list(latest_dir.glob("output_*.txt"))
        
        if not output_files:
            return None
            
        output_file = output_files[0]
        
        # 결과 파싱
        with open(output_file, 'r') as f:
            content = f.read()
        
        results = []
        sections = content.split('*')
        
        for section in sections[1:]:  # 첫 번째는 빈 문자열
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            algo_name = lines[0]
            if algo_name not in ALGORITHMS:
                continue
                
            # 각 알고리즘별 데이터 추출
            data = {
                'Server_Power': server_power,
                'Network': network, 
                'Workload': workload,
                'Section': algo_name,
                'Power': None,
                'Util': None,
                'CPU_Power': None,
                'Memory_Power': None,
                'Network_Power': None,
                'Offloading_Ratio': None,
                'CPU_Frequency_1': None,
                'CPU_Frequency_0.5': None,
                'CPU_Frequency_0.25': None,
                'CPU_Frequency_0.125': None
            }
            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('power:'):
                    match = re.search(r'power: ([\d.]+) util: ([\d.]+)', line)
                    if match:
                        data['Power'] = float(match.group(1))
                        data['Util'] = float(match.group(2))
                
                elif line.startswith('cpu power:'):
                    match = re.search(r'cpu power: ([\d.]+) memory power: ([\d.]+) network power: ([\d.]+)', line)
                    if match:
                        data['CPU_Power'] = float(match.group(1))
                        data['Memory_Power'] = float(match.group(2))
                        data['Network_Power'] = float(match.group(3))
                
                elif line.startswith('offloading ratio:'):
                    match = re.search(r'offloading ratio: ([\d.]+)', line)
                    if match:
                        data['Offloading_Ratio'] = float(match.group(1))
                
                elif re.match(r'^\d+\s+\d+\s+\d+\s+\d+\s*$', line):
                    # CPU frequency 분포 라인
                    freqs = line.split()
                    if len(freqs) == 4:
                        data['CPU_Frequency_1'] = int(freqs[0])
                        data['CPU_Frequency_0.5'] = int(freqs[1])
                        data['CPU_Frequency_0.25'] = int(freqs[2])
                        data['CPU_Frequency_0.125'] = int(freqs[3])
            
            results.append(data)
            
        # 백업 저장
        backup_name = f"exp_{server_power}_{network}_{workload:.1f}_{int(time.time())}"
        shutil.copytree(latest_dir, self.backup_dir / backup_name)
        
        return results
    
    def run_all_experiments(self):
        """모든 실험 수행"""
        total_experiments = len(list(product(
            EXPERIMENTS["server_power"],
            EXPERIMENTS["network"], 
            EXPERIMENTS["workload"]
        )))
        
        print(f"총 {total_experiments}개 실험 수행 예정")
        
        exp_count = 0
        for server_power, network, workload in product(
            EXPERIMENTS["server_power"],
            EXPERIMENTS["network"],
            EXPERIMENTS["workload"]
        ):
            exp_count += 1
            print(f"\n진행률: {exp_count}/{total_experiments}")
            
            results = self.run_experiment(server_power, network, workload)
            if results:
                self.results.extend(results)
                print(f"  결과 수집: {len(results)}개 알고리즘")
            else:
                print(f"  실험 실패 또는 결과 없음")
                
        print(f"\n전체 실험 완료! 총 {len(self.results)}개 결과 수집")
    
    def save_results(self):
        """결과를 CSV로 저장"""
        if not self.results:
            print("저장할 결과가 없습니다.")
            return
            
        fieldnames = [
            'Server_Power', 'Network', 'Workload', 'Section', 'Power', 'Util',
            'CPU_Power', 'Memory_Power', 'Network_Power', 'Offloading_Ratio',
            'CPU_Frequency_1', 'CPU_Frequency_0.5', 'CPU_Frequency_0.25', 'CPU_Frequency_0.125'
        ]
        
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"결과 저장 완료: {RESULTS_FILE}")
        print(f"백업 저장 위치: {self.backup_dir}")

def main():
    runner = ExperimentRunner()
    
    try:
        runner.run_all_experiments()
        runner.save_results()
    except KeyboardInterrupt:
        print("\n실험이 중단되었습니다.")
        if runner.results:
            runner.save_results()
    except Exception as e:
        print(f"오류 발생: {e}")
        if runner.results:
            runner.save_results()

if __name__ == "__main__":
    main()

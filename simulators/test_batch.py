#!/usr/bin/env python3
"""
배치 실험 테스트 (축소 버전)
"""

import subprocess
import re
import csv
from pathlib import Path
from itertools import product
import time

# 테스트용 축소 매개변수
TEST_EXPERIMENTS = {
    "server_power": [2, 4],                  # 2개만
    "network": [0, 60],                      # 2개만  
    "workload": [0.5, 0.7],                  # 2개만
}

ALGORITHMS = ["CO-DMO-CT", "CO-DMO", "Offloading", "DVS", "Baseline"]

class TestExperimentRunner:
    def __init__(self):
        self.results = []
        
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
        task_gen_file = Path("task_gen.py")
        with open(task_gen_file, 'r') as f:
            content = f.read()
        
        util_min = max(0.1, target_util - 0.05)
        util_max = min(1.0, target_util + 0.05)
        
        content = re.sub(r'TARGET_UTIL_MIN = [\d.]+', f'TARGET_UTIL_MIN = {util_min}', content)
        content = re.sub(r'TARGET_UTIL_MAX = [\d.]+', f'TARGET_UTIL_MAX = {util_max}', content)
        
        with open(task_gen_file, 'w') as f:
            f.write(content)
        
        # 새 태스크 생성
        subprocess.run(['python', 'task_gen.py'], capture_output=True, text=True)
        self.update_task_section()
        print(f"  Workload 설정: {target_util:.1f}")
    
    def update_task_section(self):
        """task_gen.txt를 candy_cycle.conf에 반영"""
        task_gen_txt = Path("task_gen.txt")
        config_file = Path("candy_cycle.conf")
        
        if not task_gen_txt.exists():
            return
            
        with open(task_gen_txt, 'r') as f:
            lines = f.readlines()
        
        task_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        
        with open(config_file, 'r') as f:
            content = f.read()
        
        task_section = "# wcet period memreq mem_active_ratio task_size input_size output_size offloading_bool\n*task\n"
        task_section += '\n'.join(task_lines)
        
        pattern = r'# wcet period memreq.*?\*task\n.*?(?=\n\*|\Z)'
        content = re.sub(pattern, task_section, content, flags=re.DOTALL)
        
        with open(config_file, 'w') as f:
            f.write(content)
    
    def run_experiment(self, server_power, network, workload):
        """단일 실험 수행"""
        print(f"\n실험: Server={server_power}, Network={network}, Workload={workload:.1f}")
        
        self.modify_server_power(server_power)
        self.modify_workload(workload)
        
        # run_candy.py 실행 (network 매개변수 포함)
        cmd = ['python', 'run_candy.py', str(network)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  실험 실패: {result.stderr}")
            return None
        
        print(f"  실행 성공")
        
        # Network 설정 확인
        self.verify_network_setting(network)
        
        return f"실험완료: S{server_power}_N{network}_W{workload:.1f}"
    
    def verify_network_setting(self, expected_network):
        """생성된 설정에서 network 값 확인"""
        tmp_dir = Path("tmp")
        if not tmp_dir.exists():
            return
            
        result_dirs = [d for d in tmp_dir.iterdir() if d.is_dir() and d.name.startswith("output_")]
        if not result_dirs:
            return
            
        latest_dir = max(result_dirs, key=lambda x: x.stat().st_mtime)
        conf_files = list(latest_dir.glob("conf/*.conf"))
        
        if conf_files:
            conf_file = conf_files[0]
            with open(conf_file, 'r') as f:
                content = f.read()
                
            if "*network" in content:
                lines = content.split('\n')
                in_network = False
                
                for line in lines:
                    if line.strip() == "*network":
                        in_network = True
                        continue
                    if in_network and (line.strip() == '' or line.startswith('*')):
                        break
                    if in_network and line.strip() and not line.startswith('#'):
                        parts = line.strip().split()
                        if len(parts) >= 1:
                            actual_bw = parts[0]
                            if actual_bw == str(expected_network):
                                print(f"  ✅ Network 확인: {actual_bw}")
                            else:
                                print(f"  ❌ Network 오류: 예상 {expected_network}, 실제 {actual_bw}")
                            break

def main():
    runner = TestExperimentRunner()
    
    total = len(list(product(
        TEST_EXPERIMENTS["server_power"],
        TEST_EXPERIMENTS["network"], 
        TEST_EXPERIMENTS["workload"]
    )))
    
    print(f"테스트 실험 시작: 총 {total}개")
    
    count = 0
    for server_power, network, workload in product(
        TEST_EXPERIMENTS["server_power"],
        TEST_EXPERIMENTS["network"],
        TEST_EXPERIMENTS["workload"]
    ):
        count += 1
        print(f"\n[{count}/{total}]")
        result = runner.run_experiment(server_power, network, workload)
        if result:
            runner.results.append(result)
    
    print(f"\n테스트 완료! 성공한 실험: {len(runner.results)}개")
    for result in runner.results:
        print(f"  - {result}")

if __name__ == "__main__":
    main()

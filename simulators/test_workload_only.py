#!/usr/bin/env python3
"""
Workload만 변경하는 테스트 (Server=2, Network=60 고정)
"""

import subprocess
import re
import shutil
import csv
import os
from pathlib import Path
import time

# 작업 디렉토리를 simulators로 변경
os.chdir(Path(__file__).parent.absolute())
print(f"작업 디렉토리: {Path.cwd()}")

# 테스트 매개변수 (workload만 변경)
TEST_SERVER_POWER = 2
TEST_NETWORK = 60
TEST_WORKLOADS = [0.3, 0.7, 0.9]  # 3개만 테스트

ALGORITHMS = ["CO-DMO-DT", "CO-DMO", "Offloading", "DVS", "Baseline"]

class WorkloadTestRunner:
    def __init__(self):
        self.results = []
        
    def modify_server_power(self, power):
        """cloud computation_power 수정"""
        config_file = Path("candy_cycle.conf")
        with open(config_file, 'r') as f:
            content = f.read()
        
        pattern = r'(\*cloud\nmec\s+)\d+(\s+400\s+100\s+100000\s+1\.0)'
        replacement = rf'\g<1>{power}\g<2>'
        content = re.sub(pattern, replacement, content)
        
        with open(config_file, 'w') as f:
            f.write(content)
        print(f"  ✅ Server power 설정: {power}")
    
    def modify_workload(self, target_util):
        """task_gen.py TARGET_UTIL 수정 및 태스크 재생성"""
        task_gen_file = Path("task_gen.py")
        
        if not task_gen_file.exists():
            print(f"  ❌ 오류: {task_gen_file} 파일을 찾을 수 없습니다.")
            return False
            
        print(f"  🔧 task_gen.py 수정 중...")
            
        with open(task_gen_file, 'r') as f:
            content = f.read()
        
        util_min = max(0.1, target_util - 0.05)
        util_max = min(1.0, target_util + 0.05)
        
        print(f"     TARGET_UTIL 범위: {util_min:.2f} ~ {util_max:.2f}")
        
        old_content = content
        content = re.sub(r'TARGET_UTIL_MIN = [\d.]+', f'TARGET_UTIL_MIN = {util_min}', content)
        content = re.sub(r'TARGET_UTIL_MAX = [\d.]+', f'TARGET_UTIL_MAX = {util_max}', content)
        
        if content == old_content:
            print(f"  ⚠️  경고: TARGET_UTIL 값이 수정되지 않았습니다.")
            return False
        
        with open(task_gen_file, 'w') as f:
            f.write(content)
        
        print(f"  🏗️  새 태스크 생성 중...")
        result = subprocess.run(['python', 'task_gen.py'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ 태스크 생성 오류: {result.stderr}")
            return False
        
        print(f"  ✅ 태스크 생성 완료")
        
        # candy_cycle.conf 업데이트
        success = self.update_task_section()
        if success:
            print(f"  ✅ Workload 설정 완료: {target_util:.1f}")
        
        return success
    
    def update_task_section(self):
        """task_gen.txt를 candy_cycle.conf에 반영"""
        task_gen_txt = Path("task_gen.txt")
        config_file = Path("candy_cycle.conf")
        
        if not task_gen_txt.exists():
            print(f"     ❌ {task_gen_txt} 파일을 찾을 수 없습니다.")
            return False
            
        print(f"     📖 task_gen.txt에서 태스크 읽는 중...")
        
        with open(task_gen_txt, 'r') as f:
            lines = f.readlines()
        
        task_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        print(f"     📊 읽은 태스크 개수: {len(task_lines)}")
        
        with open(config_file, 'r') as f:
            content = f.read()
        
        task_section = "# wcet period memreq mem_active_ratio task_size input_size output_size offloading_bool\n*task\n"
        task_section += '\n'.join(task_lines)
        
        old_content = content
        pattern = r'# wcet period memreq.*?\*task\n.*?(?=\n\*|\Z)'
        content = re.sub(pattern, task_section, content, flags=re.DOTALL)
        
        if content == old_content:
            print(f"     ⚠️  candy_cycle.conf의 *task 섹션이 수정되지 않았습니다.")
            return False
        else:
            print(f"     ✅ candy_cycle.conf *task 섹션 업데이트 완료")
        
        with open(config_file, 'w') as f:
            f.write(content)
        
        return True
    
    def run_single_experiment(self, workload):
        """단일 workload 실험 수행"""
        print(f"\n{'='*50}")
        print(f"🧪 실험: Server={TEST_SERVER_POWER}, Network={TEST_NETWORK}, Workload={workload:.1f}")
        print(f"{'='*50}")
        
        # 매개변수 설정
        self.modify_server_power(TEST_SERVER_POWER)
        
        if not self.modify_workload(workload):
            print(f"  ❌ Workload 설정 실패")
            return None
        
        # run_candy.py 실행
        cmd = ['python', 'run_candy.py', str(TEST_NETWORK), str(workload)]
        print(f"  🚀 실행 명령: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  ❌ 실험 실패: {result.stderr}")
            return None
        
        print(f"  ✅ 시뮬레이션 완료")
        print(f"     출력: {result.stdout.strip()}")
        
        # 결과 파싱
        results = self.parse_results(workload)
        if results:
            print(f"  📊 결과 수집: {len(results)}개 알고리즘")
            
            # 간단한 결과 미리보기
            for r in results:
                print(f"     - {r['Section']}: Power={r['Power']:.2f}, Util={r['Util']:.4f}")
        
        return results
    
    def parse_results(self, workload):
        """결과 파싱"""
        tmp_dir = Path("tmp")
        if not tmp_dir.exists():
            print(f"  ⚠️  tmp 디렉토리가 없습니다.")
            return None
            
        result_dirs = [d for d in tmp_dir.iterdir() if d.is_dir() and d.name.startswith("output_")]
        if not result_dirs:
            print(f"  ⚠️  결과 디렉토리를 찾을 수 없습니다.")
            return None
            
        latest_dir = max(result_dirs, key=lambda x: x.stat().st_mtime)
        print(f"  📁 결과 디렉토리: {latest_dir}")
        
        output_files = list(latest_dir.glob("output_*.txt"))
        if not output_files:
            print(f"  ⚠️  출력 파일을 찾을 수 없습니다.")
            return None
            
        output_file = output_files[0]
        print(f"  📄 출력 파일: {output_file}")
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        results = []
        sections = content.split('*')
        
        for section in sections[1:]:
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            algo_name = lines[0]
            if algo_name not in ALGORITHMS:
                continue
                
            data = {
                'Server_Power': TEST_SERVER_POWER,
                'Network': TEST_NETWORK, 
                'Workload': workload,
                'Section': algo_name,
                'Power': None,
                'Util': None,
                'CPU_Power': None,
                'Memory_Power': None,
                'Network_Power': None,
                'Offloading_Ratio': None
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
            
            results.append(data)
        
        return results
    
    def run_workload_test(self):
        """모든 workload 테스트 실행"""
        print(f"🎯 Workload 테스트 시작 (Server={TEST_SERVER_POWER}, Network={TEST_NETWORK} 고정)")
        print(f"📋 테스트할 Workload: {TEST_WORKLOADS}")
        
        for workload in TEST_WORKLOADS:
            results = self.run_single_experiment(workload)
            if results:
                self.results.extend(results)
            
            time.sleep(1)  # 잠깐 대기
        
        print(f"\n{'='*60}")
        print(f"📊 WORKLOAD 테스트 결과 비교")
        print(f"{'='*60}")
        
        if self.results:
            # 결과 비교 출력
            workload_results = {}
            for result in self.results:
                wl = result['Workload']
                algo = result['Section']
                if wl not in workload_results:
                    workload_results[wl] = {}
                workload_results[wl][algo] = result
            
            print(f"{'Workload':<10} {'Algorithm':<12} {'Power':<8} {'Util':<8} {'CPU_Power':<10} {'Offload_Ratio':<12}")
            print("-" * 70)
            
            for wl in sorted(workload_results.keys()):
                for algo in ALGORITHMS:
                    if algo in workload_results[wl]:
                        r = workload_results[wl][algo]
                        power = r['Power'] or 0
                        util = r['Util'] or 0
                        cpu_power = r['CPU_Power'] or 0
                        offload_ratio = r['Offloading_Ratio'] or 0
                        print(f"{wl:<10.1f} {algo:<12} {power:<8.2f} {util:<8.4f} {cpu_power:<10.2f} {offload_ratio:<12.4f}")
            
            # CSV 저장
            csv_file = Path("workload_test_results.csv")
            fieldnames = ['Server_Power', 'Network', 'Workload', 'Section', 'Power', 'Util', 
                         'CPU_Power', 'Memory_Power', 'Network_Power', 'Offloading_Ratio']
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"\n💾 결과 저장: {csv_file}")
            print(f"📈 총 결과 수: {len(self.results)}")
        else:
            print("❌ 수집된 결과가 없습니다.")

def main():
    runner = WorkloadTestRunner()
    runner.run_workload_test()

if __name__ == "__main__":
    main()

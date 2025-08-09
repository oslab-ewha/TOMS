#!/usr/bin/env python3
"""
배치 실험 테스트 (workload + network 검증)
"""

import subprocess
import time
from pathlib import Path

# 테스트 케이스
test_cases = [
    {"server": 2, "network": 30, "workload": 0.3},
    {"server": 4, "network": 90, "workload": 0.7},
]

def test_single_experiment(server, network, workload):
    """단일 실험 테스트"""
    print(f"\n=== 테스트: Server={server}, Network={network}, Workload={workload} ===")
    
    # run_candy.py 직접 실행
    cmd = ['python', 'run_candy.py', str(network), str(workload)]
    print(f"실행 명령: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 실행 실패: {result.stderr}")
        return False
    
    print(f"✅ 실행 성공")
    
    # 결과 검증
    return verify_results(network, workload)

def verify_results(expected_network, expected_workload):
    """결과 검증"""
    tmp_dir = Path("tmp")
    if not tmp_dir.exists():
        print("❌ tmp 디렉토리 없음")
        return False
    
    # 가장 최근 디렉토리 찾기
    result_dirs = [d for d in tmp_dir.iterdir() if d.is_dir() and d.name.startswith("output_")]
    if not result_dirs:
        print("❌ 결과 디렉토리 없음")
        return False
    
    latest_dir = max(result_dirs, key=lambda x: x.stat().st_mtime)
    print(f"결과 디렉토리: {latest_dir}")
    
    # Workload 검증 (디렉토리 이름에서)
    if f"output_{expected_workload}" in str(latest_dir):
        print(f"✅ Workload 검증 성공: {expected_workload}")
    else:
        print(f"❌ Workload 검증 실패: 예상 {expected_workload}, 실제 {latest_dir}")
        return False
    
    # Network 검증 (설정 파일에서)
    conf_files = list(latest_dir.glob("conf/*.conf"))
    if not conf_files:
        print("❌ 설정 파일 없음")
        return False
    
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
                        print(f"✅ Network 검증 성공: {actual_bw}")
                        return True
                    else:
                        print(f"❌ Network 검증 실패: 예상 {expected_network}, 실제 {actual_bw}")
                        return False
                break
    
    print("❌ Network 섹션을 찾을 수 없음")
    return False

def main():
    print("Workload + Network 통합 테스트 시작")
    
    success_count = 0
    for test_case in test_cases:
        if test_single_experiment(**test_case):
            success_count += 1
        time.sleep(2)  # 잠깐 대기
    
    print(f"\n테스트 결과: {success_count}/{len(test_cases)} 성공")

if __name__ == "__main__":
    main()

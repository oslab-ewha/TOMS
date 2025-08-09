#!/usr/bin/env python3
"""
Network 설정 테스트 스크립트
"""

import subprocess
import time
from pathlib import Path

# 테스트용 네트워크 값들
test_networks = [10, 60, 120]

def test_network_setting(network_val):
    """특정 network 값으로 테스트"""
    print(f"\n=== Network {network_val} 테스트 ===")
    
    # run_candy.py 실행
    cmd = ['python', 'run_candy.py', str(network_val)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"실행 실패: {result.stderr}")
        return
        
    print(f"실행 성공: {result.stdout}")
    
    # 가장 최근 결과 디렉토리 찾기
    tmp_dir = Path("tmp")
    result_dirs = [d for d in tmp_dir.iterdir() if d.is_dir() and d.name.startswith("output_")]
    if not result_dirs:
        print("결과 디렉토리를 찾을 수 없음")
        return
        
    latest_dir = max(result_dirs, key=lambda x: x.stat().st_mtime)
    
    # 첫 번째 설정 파일에서 network 확인
    conf_files = list(latest_dir.glob("conf/*.conf"))
    if conf_files:
        conf_file = conf_files[0]
        print(f"설정 파일: {conf_file}")
        
        # network 섹션 읽기
        with open(conf_file, 'r') as f:
            content = f.read()
            
        if "*network" in content:
            lines = content.split('\n')
            in_network = False
            network_lines = []
            
            for line in lines:
                if line.strip() == "*network":
                    in_network = True
                    continue
                if in_network and (line.strip() == '' or line.startswith('*')):
                    break
                if in_network and line.strip() and not line.startswith('#'):
                    network_lines.append(line.strip())
            
            if network_lines:
                print(f"Network 설정 확인:")
                for i, line in enumerate(network_lines[:3]):  # 처음 3줄만
                    print(f"  {line}")
                if len(network_lines) > 3:
                    print(f"  ... (총 {len(network_lines)}줄)")
                    
                # 첫 번째 줄에서 대역폭 확인
                first_line = network_lines[0].split()
                if len(first_line) >= 2:
                    actual_bw = first_line[0]
                    expected_bw = str(network_val)
                    if actual_bw == expected_bw:
                        print(f"✅ Network 설정 정상: {actual_bw}")
                    else:
                        print(f"❌ Network 설정 오류: 예상 {expected_bw}, 실제 {actual_bw}")
        else:
            print("❌ *network 섹션을 찾을 수 없음")

def main():
    print("Network 설정 테스트 시작")
    
    for network in test_networks:
        test_network_setting(network)
        time.sleep(1)  # 잠깐 대기
        
    print("\n테스트 완료")

if __name__ == "__main__":
    main()

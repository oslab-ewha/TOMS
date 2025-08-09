#!/usr/bin/env python3
"""
modify_workload 함수 단독 테스트
"""

import subprocess
import re
import os
from pathlib import Path

def test_modify_workload(target_util):
    """workload 수정 테스트"""
    print(f"\n=== Workload {target_util} 테스트 ===")
    
    # 1. task_gen.py 수정 전 상태 확인
    task_gen_file = Path("task_gen.py")
    with open(task_gen_file, 'r') as f:
        content = f.read()
    
    # 현재 TARGET_UTIL 값 추출
    util_min_match = re.search(r'TARGET_UTIL_MIN = ([\d.]+)', content)
    util_max_match = re.search(r'TARGET_UTIL_MAX = ([\d.]+)', content)
    
    if util_min_match and util_max_match:
        print(f"수정 전 - MIN: {util_min_match.group(1)}, MAX: {util_max_match.group(1)}")
    
    # 2. TARGET_UTIL_MIN, MAX 수정
    util_min = max(0.1, target_util - 0.05)
    util_max = min(1.0, target_util + 0.05)
    
    print(f"수정할 값 - MIN: {util_min}, MAX: {util_max}")
    
    # 정규표현식으로 수정
    old_content = content
    content = re.sub(r'TARGET_UTIL_MIN = [\d.]+', f'TARGET_UTIL_MIN = {util_min}', content)
    content = re.sub(r'TARGET_UTIL_MAX = [\d.]+', f'TARGET_UTIL_MAX = {util_max}', content)
    
    if content == old_content:
        print("❌ TARGET_UTIL 값이 수정되지 않았습니다.")
        return False
    
    # 파일 저장
    with open(task_gen_file, 'w') as f:
        f.write(content)
    
    # 3. 수정 후 확인
    with open(task_gen_file, 'r') as f:
        content = f.read()
    
    util_min_match = re.search(r'TARGET_UTIL_MIN = ([\d.]+)', content)
    util_max_match = re.search(r'TARGET_UTIL_MAX = ([\d.]+)', content)
    
    if util_min_match and util_max_match:
        actual_min = float(util_min_match.group(1))
        actual_max = float(util_max_match.group(1))
        print(f"수정 후 - MIN: {actual_min}, MAX: {actual_max}")
        
        if abs(actual_min - util_min) < 0.001 and abs(actual_max - util_max) < 0.001:
            print("✅ TARGET_UTIL 수정 성공")
        else:
            print("❌ TARGET_UTIL 수정 실패")
            return False
    
    # 4. task_gen.py 실행
    print("태스크 생성 중...")
    result = subprocess.run(['python', 'task_gen.py'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 태스크 생성 실패: {result.stderr}")
        return False
    
    print("✅ 태스크 생성 성공")
    
    # 5. 생성된 task_gen.txt 확인
    task_gen_txt = Path("task_gen.txt")
    if task_gen_txt.exists():
        with open(task_gen_txt, 'r') as f:
            lines = f.readlines()
        task_count = len([line for line in lines if line.strip() and not line.startswith('#')])
        print(f"✅ 생성된 태스크 개수: {task_count}")
        
        # 처음 3개 태스크 출력
        print("처음 3개 태스크:")
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                print(f"  {line.strip()}")
                if i >= 2:
                    break
        return True
    else:
        print("❌ task_gen.txt 파일이 생성되지 않았습니다.")
        return False

def main():
    print("modify_workload 함수 테스트 시작")
    
    test_cases = [0.3, 0.7, 0.9]
    
    for target_util in test_cases:
        success = test_modify_workload(target_util)
        if not success:
            print(f"❌ {target_util} 테스트 실패")
            break
    else:
        print("\n✅ 모든 테스트 성공!")

if __name__ == "__main__":
    main()

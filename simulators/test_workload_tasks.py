#!/usr/bin/env python3
"""
Workload별 task 생성 비교 테스트
- 각 workload에 대해 task를 생성하고 utilization 계산
- 실제로 workload가 반영되는지 확인
"""

import subprocess
import re
from pathlib import Path
import shutil

def modify_and_generate_tasks(target_util):
    """특정 workload로 task 생성"""
    print(f"\n=== Workload {target_util} 태스크 생성 ===")
    
    # 1. task_gen.py 수정
    task_gen_file = Path("task_gen.py")
    with open(task_gen_file, 'r') as f:
        content = f.read()
    
    util_min = max(0.1, target_util - 0.05)
    util_max = min(1.0, target_util + 0.05)
    
    print(f"TARGET_UTIL 범위: {util_min:.2f} ~ {util_max:.2f}")
    
    content = re.sub(r'TARGET_UTIL_MIN = [\d.]+', f'TARGET_UTIL_MIN = {util_min}', content)
    content = re.sub(r'TARGET_UTIL_MAX = [\d.]+', f'TARGET_UTIL_MAX = {util_max}', content)
    
    with open(task_gen_file, 'w') as f:
        f.write(content)
    
    # 2. task 생성
    result = subprocess.run(['python', 'task_gen.py'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 태스크 생성 실패: {result.stderr}")
        return None
    
    print("태스크 생성 출력:")
    print(result.stdout)
    
    # 3. 생성된 task 분석
    task_gen_txt = Path("task_gen.txt")
    if not task_gen_txt.exists():
        print("❌ task_gen.txt 파일이 생성되지 않았음")
        return None
    
    with open(task_gen_txt, 'r') as f:
        lines = f.readlines()
    
    tasks = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            parts = line.split('\t')
            if len(parts) >= 8:
                wcet = int(parts[0])
                period = int(parts[1])
                memreq = int(parts[2])
                offloading = int(parts[7])
                utilization = wcet / period
                tasks.append({
                    'wcet': wcet,
                    'period': period,
                    'memreq': memreq,
                    'utilization': utilization,
                    'offloading': offloading
                })
    
    # 4. 결과 분석
    if tasks:
        total_util = sum(task['utilization'] for task in tasks)
        local_tasks = [t for t in tasks if t['offloading'] == 0]
        offload_tasks = [t for t in tasks if t['offloading'] == 1]
        
        local_util = sum(t['utilization'] for t in local_tasks)
        offload_util = sum(t['utilization'] for t in offload_tasks)
        
        print(f"✅ 생성된 태스크 개수: {len(tasks)}")
        print(f"   - Local 태스크: {len(local_tasks)}개 (util: {local_util:.4f})")
        print(f"   - Offload 태스크: {len(offload_tasks)}개 (util: {offload_util:.4f})")
        print(f"   - 총 Utilization: {total_util:.4f}")
        print(f"   - 평균 Period: {sum(t['period'] for t in tasks) / len(tasks):.1f}")
        print(f"   - 평균 WCET: {sum(t['wcet'] for t in tasks) / len(tasks):.1f}")
        
        # 백업 저장
        backup_name = f"task_gen_{target_util}.txt"
        shutil.copy(task_gen_txt, backup_name)
        print(f"   - 백업 저장: {backup_name}")
        
        return {
            'target_util': target_util,
            'total_util': total_util,
            'task_count': len(tasks),
            'local_count': len(local_tasks),
            'offload_count': len(offload_tasks),
            'local_util': local_util,
            'offload_util': offload_util,
            'avg_period': sum(t['period'] for t in tasks) / len(tasks),
            'avg_wcet': sum(t['wcet'] for t in tasks) / len(tasks),
            'tasks': tasks
        }
    
    return None

def compare_tasks():
    """여러 workload로 생성된 task들 비교"""
    workloads = [0.3, 0.5, 0.7, 0.9]
    results = []
    
    for workload in workloads:
        result = modify_and_generate_tasks(workload)
        if result:
            results.append(result)
    
    if len(results) >= 2:
        print(f"\n{'='*60}")
        print("WORKLOAD별 태스크 생성 결과 비교")
        print(f"{'='*60}")
        
        print(f"{'Workload':<10} {'총 Util':<10} {'Local Util':<12} {'Offload Util':<14} {'평균 Period':<12} {'평균 WCET':<10}")
        print("-" * 60)
        
        for r in results:
            print(f"{r['target_util']:<10.1f} {r['total_util']:<10.4f} {r['local_util']:<12.4f} {r['offload_util']:<14.4f} {r['avg_period']:<12.1f} {r['avg_wcet']:<10.1f}")
        
        # 변화량 확인
        print(f"\n변화량 분석:")
        for i in range(1, len(results)):
            prev = results[i-1]
            curr = results[i]
            
            util_change = curr['total_util'] - prev['total_util']
            period_change = curr['avg_period'] - prev['avg_period']
            wcet_change = curr['avg_wcet'] - prev['avg_wcet']
            
            print(f"  {prev['target_util']:.1f} → {curr['target_util']:.1f}:")
            print(f"    Total Util: {util_change:+.4f}")
            print(f"    평균 Period: {period_change:+.1f}")
            print(f"    평균 WCET: {wcet_change:+.1f}")
        
        # 결론
        total_util_range = max(r['total_util'] for r in results) - min(r['total_util'] for r in results)
        period_range = max(r['avg_period'] for r in results) - min(r['avg_period'] for r in results)
        
        print(f"\n결론:")
        if total_util_range > 0.1:
            print(f"✅ Workload에 따라 utilization이 적절히 변화함 (범위: {total_util_range:.4f})")
        else:
            print(f"❌ Workload에 따른 utilization 변화가 미미함 (범위: {total_util_range:.4f})")
            
        if period_range > 1000:
            print(f"✅ Period 값이 적절히 조정됨 (범위: {period_range:.1f})")
        else:
            print(f"⚠️  Period 변화가 작음 (범위: {period_range:.1f})")

def main():
    print("Workload별 Task 생성 비교 테스트 시작")
    compare_tasks()

if __name__ == "__main__":
    main()

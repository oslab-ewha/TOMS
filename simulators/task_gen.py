#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Candy-Box 스타일 태스크 생성기
- 4유형: NPP(센싱), PP(룰/시스템), NCED(비중요 이벤트), CED(중요 이벤트)
- 코드 내부에서 비율/개수/목표 이용률 조정
- Σ(wcet/period) 타겟 범위로 자동 보정(Period 스케일)
- 결과: task_gen.txt 저장 (gastask 포맷)
"""

from pathlib import Path
import random
import math
from statistics import mean

# --------------------
# 설정 (여기만 바꿔 쓰면 됨)
# --------------------
SEED = 42
TOTAL_TASKS = 80
TOTAL_MEMORY = 1000  # 시스템 총 메모리 (MB)
MEMORY_SAFETY = 0.9  # 메모리 사용률 안전 마진 (90%)

RATIOS = {           # 유형 비율 합=1.0
    "NPP": 0.20,     # 센싱(주기, 낮은 WCET)
    "PP":  0.20,     # 룰/시스템(주기, 중간 WCET)
    "NCED":0.20,     # 비중요 이벤트(비주기성 가정, 주기=Deadline 윈도)
    "CED": 0.40,     # 중요 이벤트(비주기성, 높은 우선순위)
}

# 목표 이용률 구간 (Σ wcet/period)
TARGET_UTIL_MIN = 0.6499999999999999
TARGET_UTIL_MAX = 0.75

# 오프로딩 여부 기본값(유형별). 필요하면 바꿔도 됨.
OFFLOAD_FLAG = {
    "NPP": 0,
    "PP":  1,
    "NCED":1,
    "CED": 1,
}

# 메모리 요구량 자동 계산 (태스크 개수와 총 메모리에 맞춤)
avg_memreq = (TOTAL_MEMORY * MEMORY_SAFETY) / TOTAL_TASKS
MEMREQ_RANGE = (int(avg_memreq * 0.7), int(avg_memreq * 1.3))
MEM_ACTIVE_RATIO = (0.05, 0.14)
TASK_SIZE = (1200, 2000)
INPUT_SIZE = (300, 800)
OUTPUT_SIZE = (300, 800)

# WCET/Period 템플릿 (ms) - 논문 Table 3을 반영
#   NPP: 10ms 센싱, 주기는 수백~수천 ms
#   PP:  300ms 룰/시스템, 주기는 수천 ms
#   (N)CED: 520ms 액추에이터, 주기는 수천~만 ms
TEMPLATES = {
    "NPP":  {"wcet": (9, 12),     "period": (500, 2000)},   # ~10ms
    "PP":   {"wcet": (280, 320),  "period": (2000, 6000)},  # ~300ms
    "NCED": {"wcet": (500, 540),  "period": (4000, 10000)}, # ~520ms
    "CED":  {"wcet": (500, 540),  "period": (3000, 8000)},  # 좀 더 타이트한 윈도
}

OUT_FILE = Path("task_gen.txt")

# --------------------
# 유틸
# --------------------
def uni(a, b):  # 정수 균등
    return random.randint(a, b)

def uni_f(a, b):  # 실수 균등
    return random.uniform(a, b)

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# --------------------
# 태스크 샘플러
# --------------------
def sample_task(t):
    wc = uni(*TEMPLATES[t]["wcet"])
    pr = uni(*TEMPLATES[t]["period"])
    # period > wcet 보장(여유 15% 확보)
    if pr <= wc:
        pr = int(math.ceil(wc * 1.15))
    memreq = uni(*MEMREQ_RANGE)
    mem_act = round(uni_f(*MEM_ACTIVE_RATIO), 4)
    tsize = uni(*TASK_SIZE)
    isize = uni(*INPUT_SIZE)
    osize = uni(*OUTPUT_SIZE)
    off   = OFFLOAD_FLAG[t]
    return [wc, pr, memreq, mem_act, tsize, isize, osize, off]

def build_counts(total, ratios):
    # 비율→정수 개수, 합 보정
    base = {k: int(total * v) for k, v in ratios.items()}
    # 모자라는 만큼 큰 비율부터 채움
    deficit = total - sum(base.values())
    if deficit > 0:
        order = sorted(ratios.items(), key=lambda kv: kv[1], reverse=True)
        i = 0
        while deficit > 0:
            base[order[i % len(order)][0]] += 1
            deficit -= 1
            i += 1
    return base

def sum_util(tasks):
    return sum(w/p for w, p, *_ in tasks)

def scale_periods(tasks, target_min, target_max):
    """
    Σ(w/p)를 target 범위에 들게 period 전체 스케일.
    - 과도한 스케일로 period <= wcet 되는 일 없도록 안전마진 유지(1.1*wcet).
    """
    cur = sum_util(tasks)
    if target_min <= cur <= target_max:
        return tasks, 1.0

    # 목표 중앙으로 수렴시키기
    target = (target_min + target_max) / 2
    # Σ(w/p_new) = target  =>  p_new = p * (cur/target)
    factor = cur / target if cur > 0 else 1.0

    new = []
    for (w, p, mem, ma, ts, ins, outs, off) in tasks:
        new_p = int(math.ceil(p * factor))
        # 안전 마진: period >= ceil(1.10 * wcet)
        min_safe = int(math.ceil(w * 1.10))
        if new_p < min_safe:
            new_p = min_safe
        new.append([w, new_p, mem, ma, ts, ins, outs, off])

    return new, factor

# --------------------
# 메인
# --------------------
def main():
    random.seed(SEED)
    counts = build_counts(TOTAL_TASKS, RATIOS)

    tasks = []
    by_type = {k: [] for k in RATIOS.keys()}

    for t, cnt in counts.items():
        for _ in range(cnt):
            row = sample_task(t)
            tasks.append(row)
            by_type[t].append(row)

    # 이용률 보정
    tasks, scale = scale_periods(tasks, TARGET_UTIL_MIN, TARGET_UTIL_MAX)

    # 저장
    with OUT_FILE.open("w", encoding="utf-8") as f:
        f.write("# wcet period memreq mem_active_ratio task_size input_size output_size offloading_bool\n")
        for row in tasks:
            wc, pr, mem, ma, ts, ins, outs, off = row
            f.write(f"{wc}\t{pr}\t{mem}\t{ma}\t{ts}\t{ins}\t{outs}\t{off}\n")

    # 통계 출력
    total_u = sum_util(tasks)
    print(f"• 총 태스크: {len(tasks)}  (분포: {counts})")
    print(f"• Σ(wcet/period) = {total_u:.6f}  (타겟 [{TARGET_UTIL_MIN}, {TARGET_UTIL_MAX}]), period 스케일 계수 ×{scale:.3f}")

    for t, lst in by_type.items():
        if not lst: 
            continue
        u = sum(w/p for w, p, *_ in lst)
        avg_w = mean(w for w, *_ in lst)
        avg_p = mean(p for _, p, *_ in lst)
        print(f"  - {t:5s}: {len(lst):2d}개, ΣU={u:.4f}, avg_wcet={avg_w:.1f} ms, avg_period={avg_p:.1f} ms")

    # 추천: 추가 지표
    avg_mem = mean(row[2] for row in tasks)
    avg_mact = mean(row[3] for row in tasks)
    off_rate = mean(row[7] for row in tasks)
    print(f"• 평균 memreq={avg_mem:.1f}, 평균 mem_active_ratio={avg_mact:.3f}, 오프로딩 비율={off_rate*100:.1f}%")

if __name__ == "__main__":
    main()

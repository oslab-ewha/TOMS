import random
import csv

# ==========================
# 🎛 설정값 (수정 가능)
# ==========================

N_TASKS = 100
MEM_TOTAL = 2000        # 전체 시스템 메모리
UTIL_CPU = 0.7          # TEE 오버헤드 고려하여 더욱 감소
UTIL_TARGET = 0.8       # TEE 오버헤드 고려하여 더욱 감소

TASK_TYPES = {
    "CED": {
        "ratio": 0.2,
        "wcet_range": (200, 400),     # WCET 감소
        "period_factor": (40, 50),    # Period factor 크게 증가
        "task_size": (5000, 6000),
        "input_size": (3000, 4000),
        "output_size": (1500, 2000)
    },
    "NCED": {
        "ratio": 0.2,
        "wcet_range": (150, 300),     # WCET 감소
        "period_factor": (35, 45),    # Period factor 크게 증가
        "task_size": (4500, 5500),
        "input_size": (2000, 3500),
        "output_size": (1200, 1800)
    },
    "PP": {
        "ratio": 0.3,
        "wcet_range": (100, 200),     # WCET 감소
        "period_factor": (30, 40),    # Period factor 크게 증가
        "task_size": (4000, 5000),
        "input_size": (1000, 2500),
        "output_size": (800, 1500)
    },
    "NPP": {
        "ratio": 0.3,
        "wcet_range": (50, 150),      # WCET 감소
        "period_factor": (25, 35),    # Period factor 크게 증가
        "task_size": (4000, 4500),
        "input_size": (800, 2000),
        "output_size": (800, 1200)
    }
}

# ==========================
# 🔧 Task 생성 함수
# ==========================

def generate_task_list(n_tasks, mem_total, util_cpu, util_target):
    # Memory requirements calculation
    avg_memreq = mem_total // n_tasks  # 평균적으로 각 태스크가 전체 메모리의 1/n을 사용
    memreq_1task = avg_memreq

    task_types = []
    for t, conf in TASK_TYPES.items():
        count = int(n_tasks * conf['ratio'])
        task_types.extend([t] * count)
    task_types += ["NPP"] * (n_tasks - len(task_types))  # 부족분 보정
    random.shuffle(task_types)

    task_list = []
    for i in range(n_tasks):
        ttype = task_types[i]
        config = TASK_TYPES[ttype]

        wcet = random.randint(*config['wcet_range'])
        period_factor = random.randint(*config['period_factor'])
        period = wcet * period_factor

        # Memory requirements based on gen_task.c
        memreq = int(memreq_1task + random.randint(-int(memreq_1task/2), int(memreq_1task/2)))
        mem_active_ratio = round(0.1 + random.uniform(-0.01, 0.01), 6)  # 0.1 ± 0.01

        task_size = random.randint(*config['task_size'])
        input_size = random.randint(*config['input_size'])
        output_size = random.randint(*config['output_size'])

        offloading = 1 if ttype in ["CED", "NCED"] else 0

        task_list.append([
            wcet, period, memreq, mem_active_ratio,
            task_size, input_size, output_size, offloading
        ])

    return task_list

# ==========================
# 💾 파일 저장 함수
# ==========================

def write_to_file(task_list, filename="candy_task_generated.txt"):
    with open(filename, "w", newline='') as f:
        writer = csv.writer(f, delimiter=' ')
        for task in task_list:
            writer.writerow(task)

# ==========================
# 🚀 실행
# ==========================

if __name__ == "__main__":
    tasks = generate_task_list(
        n_tasks=N_TASKS,
        mem_total=MEM_TOTAL,
        util_cpu=UTIL_CPU,
        util_target=UTIL_TARGET
    )
    write_to_file(tasks)
    print(f"✅ {len(tasks)} tasks generated → candy_task_generated.txt")

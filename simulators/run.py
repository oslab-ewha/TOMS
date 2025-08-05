# run_simulation.py
# Same as run.sh, but in Python
#!/usr/bin/env python3

import os
import argparse
import subprocess
import shutil
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path

@dataclass
class SimulationConfig:
    util_target: float
    util_cpu: float
    network_up: int
    network_down: int
    seed: int
    
class SimulationManager:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.output_dir = Path(f"./tmp/output_{config.util_target}+{os.getpid()}")
        self.setup_directories()
        
    def setup_directories(self):
        """초기 디렉토리 구조 설정"""
        dirs = ['conf', 'gen', 'report', 'task']
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
            
    def create_base_config(self, filename: str, tee_enabled: bool, 
                          offloading_enabled: bool, dvfs_enabled: bool) -> str:
        """기본 설정 파일 생성"""
        config_path = self.output_dir / 'conf' / filename
        
        with open(config_path, 'w') as f:
            # 유전 알고리즘 설정
            f.write("# max_generations n_populations cutoff penalty\n")
            f.write("*genetic\n10000 100 1.5 1.5\n\n")
            
            # 태스크 생성 설정
            f.write("# wcet_min wcet_max mem_total util_cpu util_target n_tasks task_size_min task_size_max input_size_min input_size_max output_size_min output_size_max\n")
            f.write("*gentask\n")
            f.write(f"500 1000 2000 {self.config.util_cpu} {self.config.util_target} 100 4000 6000 800 4000 800 2000\n\n")
            
            # 네트워크 설정
            f.write("# uplink_min uplink_max downlink_min downlink_max n_networks\n")
            f.write("*gennetwork\n")
            f.write(f"{self.config.network_up} {self.config.network_up} {self.config.network_down} {self.config.network_down} 100\n\n")
            
            # 네트워크 커맨더 설정
            f.write("# intercept_out_min intercept_out_max intercept_in_min intercept_in_max n_net_commanders\n")
            f.write("*gennetcommander\n")
            f.write("1 5 5 7 100\n\n")
            
            # CPU 주파수 설정
            f.write("# wcet_scale power_active power_idle\n*cpufreq\n")
            if dvfs_enabled:
                f.write("1    100    1\n0.5  25   0.25\n0.25 6.25 0.0625\n0.125 1.5625 0.015625\n")
            else:
                f.write("1    100    1\n")
                
            # 메모리 설정    
            f.write("\n# type max_capacity wcet_scale power_active power_idle\n*mem\n")
            f.write("dram  1000 1    0.01   0.01\n")
            f.write("nvram 1000 0.8  0.01   0.0001\n\n")
            
            # 클라우드 설정
            f.write("# type computation_power power_active power_idle max_capacity offloading_limit\n*cloud\n")
            f.write("mec  2   400   100   100000   1.0\n\n")
            
            # 오프로딩 설정
            f.write("# offloading_ratio\n*offloadingratio\n")
            if offloading_enabled:
                f.write("0\n1\n")
            else:
                f.write("0\n")
                
            # TEE 설정
            f.write(f"\n# TEE\n*TEE\n{int(tee_enabled)}\n\n")
            
        return str(config_path)

    def run_gasgen(self, config_file: str):
        """gasgen 실행 및 생성된 파일 병합"""
        subprocess.run(['./gasgen', config_file], check=True)
        
        # 생성된 파일들을 설정 파일에 추가
        with open(config_file, 'a') as f:
            f.write("\n# uplink_data_rate downlink_data_rate\n*network\n")
            with open('network_generated.txt', 'r') as nf:
                f.write(nf.read())
                
            f.write("\n# intercept_out intercept_in\n*netcommander\n")
            with open('network_commander_generated.txt', 'r') as nc:
                f.write(nc.read())
                
            f.write("\n# wcet period memreq mem_active_ratio task_size input_size output_size offloading_bool\n*task\n")
            with open('task_generated.txt', 'r') as tf:
                f.write(tf.read())

    def run_gastask(self, config_file: str, section_name: str):
        """gastask 실행 및 결과 저장"""
        output_file = self.output_dir / f"output_{self.config.util_target}+{self.config.network_up}.txt"
        
        # gastask 실행하고 터미널에 직접 출력
        with open(output_file, 'a') as f:
            f.write(f"\n*{section_name}\n")
        
        command = ['./gastask', '-s', str(self.config.seed), config_file]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(process.stdout, end='')  # 터미널에 출력
        
        with open(output_file, 'a') as f:
            f.write(process.stdout)  # 파일에 저장
            
        # 결과 파일 이동
        for file_name in ['task.txt', 'report.txt']:
            if os.path.exists(file_name):
                new_name = f"{file_name.split('.')[0]}_{self.config.util_target}+{self.config.network_up}+{section_name.lower()}.txt"
                shutil.move(file_name, self.output_dir / ('task' if 'task' in file_name else 'report') / new_name)

    def run_simulations(self):
        """모든 시뮬레이션 실행"""
        scenarios = [
            ("CO-DMO-CT", True, True, True),
            ("CO-DMO", False, True, True),
            ("Offloading", False, True, False),
            ("DVS", False, False, True),
            ("Baseline", False, False, False)
        ]
        
        for section_name, tee, offloading, dvfs in scenarios:
            config_file = self.create_base_config(f"gastask_{section_name.lower()}_{self.config.util_target}+{os.getpid()}.conf",
                                                tee, offloading, dvfs)
            self.run_gasgen(config_file)
            self.run_gastask(config_file, section_name)
            
        # 생성된 파일들 이동
        for file_name in ['task_generated.txt', 'network_commander_generated.txt', 'network_generated.txt']:
            if os.path.exists(file_name):
                new_name = f"gen_{file_name.split('.')[0]}_{self.config.util_target}+{os.getpid()}.txt"
                shutil.move(file_name, self.output_dir / 'gen' / new_name)
                
        print(f"Simulation completed. Results saved in {self.output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Run IIoT task simulation scenarios')
    parser.add_argument('util_target', type=float, help='Target utilization')
    parser.add_argument('util_cpu', type=float, help='CPU utilization')
    parser.add_argument('network_up', type=int, help='Uplink network bandwidth (Mbps)')
    parser.add_argument('network_down', type=int, help='Downlink network bandwidth (Mbps)')
    parser.add_argument('seed', type=int, help='Random seed')
    
    args = parser.parse_args()
    config = SimulationConfig(
        util_target=args.util_target,
        util_cpu=args.util_cpu,
        network_up=args.network_up,
        network_down=args.network_down,
        seed=args.seed
    )
    
    manager = SimulationManager(config)
    manager.run_simulations()

if __name__ == '__main__':
    main()

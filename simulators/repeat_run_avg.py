#!/usr/bin/env python3

import os
import subprocess
import shutil
from pathlib import Path
import statistics
from dataclasses import dataclass
from typing import List, Dict, Tuple
import time

@dataclass
class ExperimentConfig:
    workloads: List[float]
    network_up: int
    network_down: int
    seed: int
    iterations: int

class ResultCollector:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.tmp_dir = Path("./tmp")
        self.sections = ["CO-DMO-CT", "CO-DMO", "Offloading", "DVS", "Baseline"]
        self.metrics = ["Power", "Util", "CPU_Power", "Memory_Power", "Network_Power", 
                       "Offloading_Ratio", "CPU_Frequency_1", "CPU_Frequency_0.5", 
                       "CPU_Frequency_0.25", "CPU_Frequency_0.125"]
        self.setup_workspace()
        
    def setup_workspace(self):
        """작업 디렉토리 초기화"""
        if self.tmp_dir.exists():
            print("Removing existing tmp directory...")
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(exist_ok=True)
        
        # 결과 파일 생성
        self.result_file = self.tmp_dir / f"result_{self.config.network_up}_{self.config.network_down}_{self.config.iterations}.txt"
        with open(self.result_file, 'w') as f:
            headers = ["Workload", "Section"] + self.metrics
            f.write(" ".join(headers) + "\n")
            
    def extract_section_data(self, output_file: Path, section: str) -> Tuple[List[float], bool]:
        """특정 섹션의 데이터 추출"""
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                
            # 섹션 시작 위치 찾기
            section_marker = f"*{section}"
            if section == "CO-DMO":
                # CO-DMO-CT와 구분하기 위해 정확한 매칭
                section_content = [line for line in content.split('\n') 
                                 if line.strip() == section_marker]
                if not section_content:
                    return [], False
                section_start = content.find(f"\n{section_marker}\n")
            else:
                section_start = content.find(section_marker)
                
            if section_start == -1:
                return [], False
                
            section_content = content[section_start:].split('\n')[:10]
            
            # 데이터 추출
            power = float(next(line.split()[1] for line in section_content if line.startswith("power:")))
            util = float(next(line.split()[3] for line in section_content if line.startswith("power:")))
            
            cpu_line = next(line for line in section_content if line.startswith("cpu power:"))
            cpu_parts = cpu_line.split()
            cpu_power = float(cpu_parts[2])
            memory_power = float(cpu_parts[5])
            network_power = float(cpu_parts[8])
            
            ratio = float(next(line.split()[2] for line in section_content if line.startswith("offloading ratio:")))
            
            # CPU 주파수 데이터 추출
            freq_start = None
            for i, line in enumerate(section_content):
                if line.startswith("cpu frequency:"):
                    freq_start = i + 2
                    break
            
            if freq_start is None or freq_start >= len(section_content):
                return [], False
                
            freq_parts = section_content[freq_start].split()
            if len(freq_parts) != 4:
                return [], False
                
            freqs = [int(f) for f in freq_parts]
            
            return [power, util, cpu_power, memory_power, network_power, ratio] + freqs, True
            
        except (IndexError, ValueError, FileNotFoundError) as e:
            print(f"Error extracting data for section {section}: {str(e)}")
            return [], False
            
    def run_simulation(self, workload: float):
        """단일 시뮬레이션 실행 및 결과 수집"""
        util_cpu = workload - 0.025
        
        # 섹션별 결과 저장을 위한 딕셔너리 초기화
        section_results: Dict[str, List[List[float]]] = {section: [] for section in self.sections}
        
        for i in range(1, self.config.iterations + 1):
            print(f"Iteration {i} for workload {workload}...")
            
            # run.sh 실행
            subprocess.run([
                "./run.sh",
                str(workload), str(util_cpu),
                str(self.config.network_up), str(self.config.network_down),
                str(self.config.seed)
            ])
            
            # 가장 최근 출력 디렉토리 찾기
            output_dirs = list(self.tmp_dir.glob(f"output_{workload}+*"))
            if not output_dirs:
                print(f"Warning: No output directory found for workload {workload} iteration {i}")
                continue
                
            latest_dir = max(output_dirs, key=lambda p: p.stat().st_mtime)
            output_file = latest_dir / f"output_{workload}+{self.config.network_up}.txt"
            
            if not output_file.exists():
                print(f"Warning: Output file not found: {output_file}")
                continue
                
            # 각 섹션의 데이터 수집
            for section in self.sections:
                values, success = self.extract_section_data(output_file, section)
                if success:
                    section_results[section].append(values)
        
        return section_results
    
    def calculate_averages(self, results: Dict[str, List[List[float]]], workload: float):
        """섹션별 평균 계산 및 결과 파일에 저장"""
        with open(self.result_file, 'a') as f:
            for section in self.sections:
                if not results[section]:
                    continue
                    
                # 각 지표별 평균 계산
                averages = [statistics.mean(values[i] for values in results[section])
                          for i in range(len(self.metrics))]
                
                # 결과 저장
                result_line = f"{workload} {section} " + " ".join(f"{avg:.2f}" for avg in averages)
                f.write(result_line + "\n")
    
    def run_experiments(self):
        """모든 워크로드에 대한 실험 실행"""
        for workload in self.config.workloads:
            print(f"\nRunning workload: {workload}")
            results = self.run_simulation(workload)
            self.calculate_averages(results, workload)
            
def main():
    config = ExperimentConfig(
        workloads=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        network_up=100,
        network_down=100,
        seed=0,
        iterations=10
    )
    
    collector = ResultCollector(config)
    collector.run_experiments()

if __name__ == '__main__':
    main()

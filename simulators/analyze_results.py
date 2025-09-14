#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실험 결과 분석 및 시각화 스크립트
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_and_analyze_results():
    """결과 파일 로드 및 기본 분석"""
    results_file = Path("experiment_results.csv")
    
    if not results_file.exists():
        print("experiment_results.csv 파일이 없습니다.")
        return None
        
    df = pd.read_csv(results_file)
    
    print("=== 실험 결과 요약 ===")
    print(f"총 실험 수: {len(df)}")
    print(f"Server Power 범위: {df['Server_Power'].unique()}")
    print(f"Network 범위: {df['Network'].unique()}")
    print(f"Workload 범위: {df['Workload'].unique()}")
    print(f"알고리즘: {df['Section'].unique()}")
    print()
    
    # 알고리즘별 평균 성능
    print("=== 알고리즘별 평균 성능 ===")
    algo_avg = df.groupby('Section')[['Power', 'Util', 'Offloading_Ratio']].mean()
    print(algo_avg.round(3))
    print()
    
    # 워크로드별 성능
    print("=== 워크로드별 평균 Power 소모량 ===")
    workload_power = df.groupby(['Workload', 'Section'])['Power'].mean().unstack()
    print(workload_power.round(3))
    print()
    
    # 네트워크별 성능
    print("=== 네트워크별 평균 Power 소모량 ===")
    network_power = df.groupby(['Network', 'Section'])['Power'].mean().unstack()
    print(network_power.round(3))
    print()
    
    # 서버 파워별 성능
    print("=== 서버 파워별 평균 Power 소모량 ===")
    server_power = df.groupby(['Server_Power', 'Section'])['Power'].mean().unstack()
    print(server_power.round(3))
    
    return df

def create_visualizations(df):
    """결과 시각화"""
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 알고리즘별 파워 소모량
    df.boxplot(column='Power', by='Section', ax=axes[0,0])
    axes[0,0].set_title('알고리즘별 Power 소모량 분포')
    axes[0,0].set_xlabel('Algorithm')
    axes[0,0].set_ylabel('Power')
    
    # 2. 워크로드 vs 파워
    for algo in df['Section'].unique():
        algo_data = df[df['Section'] == algo]
        axes[0,1].plot(algo_data['Workload'], algo_data['Power'], 'o-', label=algo, alpha=0.7)
    axes[0,1].set_title('워크로드별 Power 소모량')
    axes[0,1].set_xlabel('Workload')
    axes[0,1].set_ylabel('Power')
    axes[0,1].legend()
    
    # 3. 네트워크 vs 파워
    for algo in df['Section'].unique():
        algo_data = df[df['Section'] == algo]
        axes[1,0].plot(algo_data['Network'], algo_data['Power'], 'o-', label=algo, alpha=0.7)
    axes[1,0].set_title('네트워크별 Power 소모량')
    axes[1,0].set_xlabel('Network Bandwidth')
    axes[1,0].set_ylabel('Power')
    axes[1,0].legend()
    
    # 4. 서버 파워 vs 시스템 파워
    server_power_avg = df.groupby(['Server_Power', 'Section'])['Power'].mean().reset_index()
    sns.barplot(data=server_power_avg, x='Server_Power', y='Power', hue='Section', ax=axes[1,1])
    axes[1,1].set_title('서버 파워별 평균 Power 소모량')
    
    plt.tight_layout()
    plt.savefig('experiment_analysis.png', dpi=300, bbox_inches='tight')
    print("시각화 결과 저장: experiment_analysis.png")

def find_best_configurations(df):
    """최적 구성 찾기"""
    print("\n=== 최적 구성 분석 ===")
    
    # 각 알고리즘별 최저 파워 구성
    print("알고리즘별 최저 Power 구성:")
    for algo in df['Section'].unique():
        algo_data = df[df['Section'] == algo]
        best = algo_data.loc[algo_data['Power'].idxmin()]
        print(f"{algo}: Power={best['Power']:.3f}, Server={best['Server_Power']}, "
              f"Network={best['Network']}, Workload={best['Workload']}")
    
    print("\n전체 최저 Power 구성:")
    overall_best = df.loc[df['Power'].idxmin()]
    print(f"Algorithm: {overall_best['Section']}")
    print(f"Power: {overall_best['Power']:.3f}")
    print(f"Server Power: {overall_best['Server_Power']}")
    print(f"Network: {overall_best['Network']}")
    print(f"Workload: {overall_best['Workload']}")
    print(f"Utilization: {overall_best['Util']:.3f}")
    print(f"Offloading Ratio: {overall_best['Offloading_Ratio']:.3f}")

def main():
    df = load_and_analyze_results()
    if df is not None:
        create_visualizations(df)
        find_best_configurations(df)

if __name__ == "__main__":
    main()

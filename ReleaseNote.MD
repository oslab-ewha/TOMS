# Quick Start Guide

## Part 1

1. `make` 명령어를 통해 실행 프로그램을 만든다. 만일 각 실행 프로그램이 접근 권한이 없다고 하면`chmod` 명령어를 통해 접근 권한을 변경한다. 
```
# make
```
2.  `gataskk.conf.tmpl`의 형식에 맞춰서 새로운 configuration 파일`gastask.conf`을 생성한다.
3. `gasgen`을 실행한다. 
```
# ./gasgen gastask.conf
```
4. root 파일 내에 `task_generated.txt`, `network_generated.txt`, `network_commander_generated.txt` 가 생성된 것을 확인 할 수 있다. 해당 파일 들이 미리 정해진 테스크의 성질을 의미한다.
5. `task_generated.txt` 의 내용을 `gastask.conf` 파일의 *task 밑줄에 복사한다.
6. `network_generated.txt` 의 내용을 `gastask.conf` 파일의 *network 밑줄에 복사한다.
7. `network_commander_generated.txt` 의 내용을 `gastask.conf` 파일의 *netcommander 밑줄에 복사한다.
8. `gastask`를 실행한다. 
```
# ./gastask gastask.conf
```
9. 스케줄링 결과를 콘솔에서 확인 할 수 있다.
10. 상세 스케줄링 결과를 `task.txt`에서 확인 할 수 있다. 

## Part 2
TOVS, Offloading Only, DVFS Only, Default 값을 `gastask.conf`파일을 수정함으로 확인할 수 있다. 
### TOVS
Part1 과 같은 방법으로 실행한다. 
### Offloading Only
  1. TOVS에서 사용한 `gastask.conf`파일의 *cpufreq 아래 부분의 첫째줄을 제외하고 주석처리한다. 
```
  # wcet_sacle power_active power_idle
*cpufreq
1    100    1
# 0.5  25   0.25
# 0.25 6.25 0.0625
# 0.125 1.5625 0.015625
```
  2. `gastask`를 실행한다. 

### DVFS Only
  1. TOVS에서 사용한 `gastask.conf`파일의 *offloadingratio 아래 부분의 첫째줄을 제외하고 주석처리한다. 
```
# offloading_ratio 
*offloadingratio
0
# 1
```
  2. `gastask`를 실행한다. 

### Default
  Offloading, DVFS 기법 모두 사용하지 않을 경우를 나타낸다.
  1. TOVS에서 사용한 `gastask.conf`파일의 *cpufreq 아래 부분의 첫째줄을 제외하고 주석처리한다. *offloadingratio 아래 부분의 첫째줄을 제외하고 주석처리한다. 
```
  # wcet_sacle power_active power_idle
*cpufreq
1    100    1
# 0.5  25   0.25
# 0.25 6.25 0.0625
# 0.125 1.5625 0.015625
...
# offloading_ratio 
*offloadingratio
0
# 1
```
  2. `gastask`를 실행한다. 

## Part 3
Part1 과 Part2의 내용을 자동화 하여 사용한다. 
Uplink 네트워크 속도가 10일때부터 120까지 10 단위로 같은 태스크에 대해 적용된다. 
1. root 폴더 내부에 tmp 폴더를 생성한다.
2. `./run.sh` (for mac) 이나 `./run2.sh`(for linux) 를 사용한다. 
   순서대로 총 Utilization, CPU Utilization, Network Uplink, Network Downlink, Seed의 값을 넣을 수 있다.
   Network Uplink와 downlink의 `10 100` 이 Default 값이다.
```
  # ./run.sh <util> <util cpu> 10 100 <seed>
```
3. tmp 폴더 내부에 `output_<util>+<pid>` 폴더에서 각 네트워크 상황별 콘솔 아웃풋 `output_<util>+<network up>.txt`을 확인한다. 각 상황별 테스크 스케줄링을 `task_<util>+<uplink>+<type>.txt`를 확인한다.

## Part 4
Part3 의 내용을 자동화 하여 반복 실행하고 workload에 따른 power, util, offloading ratio, CPU_Frequency 등의 평균을 출력한다.
1. repeat_run_avg.sh 파일의 workloads, networkUp, networkDown, seed, iterations, result_file을 세팅한다.
2. `./repeat_run_avg.sh` 를 사용한다.
```
  # ./repeat_run_avg.sh
```
3. tmp 폴더에서 result_${networkUp}_${networkDown}_${iterations}.txt를 확인한다. 해당 파일에는 네트워크 상황, workload별 Workload Section Power Util CPU_Power Memory_Power Network_Power Offloading_Ratio CPU_Frequency_1 CPU_Frequency_0.5 CPU_Frequency_0.25 CPU_Frequency_0.125의 평균값이 저장되어있다.

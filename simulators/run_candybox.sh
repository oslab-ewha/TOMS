#!/bin/bash
# run_candybox.sh
# Description:
# This script is a wrapper around run.sh that uses our custom task generator
# while maintaining the existing simulation infrastructure.

function usage() {
    cat <<EOF
Usage: run_candybox.sh <util> <util cpu> <network_up> <network_down> <seed>
EOF
}

if [ $# -lt 3 ]; then
    usage
    exit 1
fi

utilTarget=$1
utilCpu=$2
networkUp=$3
networkDown=$4
seed=$5

# 먼저 run.sh를 실행하여 기본 설정 파일과 디렉토리 구조 생성
./run.sh $utilTarget $utilCpu $networkUp $networkDown $seed | tee temp_output.txt

# 가장 최근 생성된 output 디렉토리 찾기
latest_output_dir=$(ls -td tmp/output_${utilTarget}+* | head -1)

if [[ -z "$latest_output_dir" ]]; then
    echo "Error: Could not find output directory"
    exit 1
fi

# run.sh의 출력 저장
cp temp_output.txt "$latest_output_dir/output_${utilTarget}+${networkUp}.txt"
rm temp_output.txt

# task generator로 새로운 task.txt 생성
python3 task_generator.py

# 각 시나리오 디렉토리에 새로운 task.txt 복사
for scenario in "co-dmo-ct" "co-dmo" "offloading" "dvs" "baseline"; do
    # task.txt가 존재하면 덮어쓰기
    if [ -f "task_generated.txt" ]; then
        cp task_generated.txt "$latest_output_dir/task/task_${utilTarget}+${networkUp}+${scenario}.txt"
    fi
done

# task_metadata.json도 output 디렉토리에 저장
if [ -f "task_metadata.json" ]; then
    cp task_metadata.json "$latest_output_dir/gen/"
fi

# 생성된 임시 파일 정리
rm -f task_generated.txt task_metadata.json

# 최종 결과 출력
cat "$latest_output_dir/output_${utilTarget}+${networkUp}.txt"

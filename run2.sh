function usage() {
    cat <<EOF
Usage: run2.sh <util> <util cpu> <network_up> <network_down>
EOF
}

if [ $# -lt 3 ]; then
    usage
    exit 1
fi

GASTASK=`./gastask`

GASGEN=`./gasgen`

utilTarget=$1
utilCpu=$2
networkUp=$3
networkDown=$4

gastask_conf=./tmp/gastask_$utilTarget+$$.conf
simrts_conf=/tmp/simrts$$.conf


COMMON_CONF="\
# max_generations n_populations cutoff penalty
*genetic
10000 100 1.5 1.5

# wcet_min wcet_max mem_total util_cpu util_target n_tasks task_size_min task_size_max input_size_min input_size_max output_size_min output_size_max
*gentask
500 1000 2000 $utilCpu $utilTarget 100 4000 6000 800 4000 800 2000

# uplink_min uplink_max downlink_min downlink_max n_networks
*gennetwork
$networkUp $networkUp $networkDown $networkDown 100

# intercept_out_min intercept_out_max intercept_in_min intercept_in_max n_net_commanders
*gennetcommander
1 5 5 7 100

# wcet_scale power_active power_idle
*cpufreq
1    100    1
0.5  25   0.25
0.25 6.25 0.0625
0.125 1.5625 0.015625

# type max_capacity wcet_scale power_active power_idle
*mem
dram  1000 1    0.01   0.01
nvram 1000 0.8  0.01   0.0001

# type computation_power power_active power_idle max_capacity offloading_limit
*cloud
mec  2   400   100   100000   1.0

# offloading_ratio 
*offloadingratio
0
1

# uplink_data_rate downlink_data_rate
*network"

echo "$COMMON_CONF" <<EOF >$gastask_conf
EOF

'./gasgen' $gastask_conf
cat ./network_generated.txt >>$gastask_conf

echo "
# intercept_out intercept_in
*netcommander" >>$gastask_conf

cat ./network_commander_generated.txt >>$gastask_conf

echo "
# wcet period memreq mem_active_ratio input_data_size output_data_size
*task" >>$gastask_conf

cat ./task_generated.txt >>$gastask_conf

mkdir ./tmp/output_$utilTarget+$$
OUTPUT=./tmp/output_$utilTarget+$$
mv ./task_generated.txt $OUTPUT/gen_task_generated_$utilTarget+$$.txt
mv ./network_commander_generated.txt $OUTPUT/gen_network_commander_generated_$utilTarget+$$.txt

touch $OUTPUT/output_$utilTarget+$networkUp.txt
echo "*tovs\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task_$utilTarget+$networkUp+tovs.txt
sed -i "20s/0.5/\#0.5/" $gastask_conf
sed -i "21s/0.25/\#0.25/" $gastask_conf
sed -i "22s/0.125/\#0.125/" $gastask_conf

echo "\n*offloading\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task_$utilTarget+$networkUp+offloading.txt

sed -i "20s/\#0.5/0.5/" $gastask_conf
sed -i "21s/\#0.25/0.25/" $gastask_conf
sed -i "22s/\#0.125/0.125/" $gastask_conf

sed -i "36s/1/\#1/" $gastask_conf

echo "\n*dvfs\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task_$utilTarget+$networkUp+dvfs.txt

sed -i "20s/0.5/\#0.5/" $gastask_conf
sed -i "21s/0.25/\#0.25/" $gastask_conf
sed -i "22s/0.125/\#0.125/" $gastask_conf
echo "\n*nothing\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
mv task.txt $OUTPUT/task_$utilTarget+$networkUp+nothing.txt

sed -i "20s/\#0.5/0.5/" $gastask_conf
sed -i "21s/\#0.25/0.25/" $gastask_conf
sed -i "22s/\#0.125/0.125/" $gastask_conf
sed -i "36s/\#1/1/" $gastask_conf

for var in `seq 20 10 120`
do
	var2=$(($var*10))
	var3=$(($var-10))
	var4=$(($var3*10))
	sed -i "s/$var3 $var4/$var $var2/g" $gastask_conf
	networkUp=$var
	networkDown=$var2
	touch $OUTPUT/output_$utilTarget+$networkUp.txt

	echo "*tovs\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
	'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
	mv task.txt $OUTPUT/task_$utilTarget+$networkUp+tovs.txt

	sed -i "20s/0.5/\#0.5/" $gastask_conf
	sed -i "21s/0.25/\#0.25/" $gastask_conf
	sed -i "22s/0.125/\#0.125/" $gastask_conf

	echo "\n*offloading\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
	'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
	mv task.txt $OUTPUT/task_$utilTarget+$networkUp+offloading.txt

	sed -i "20s/\#0.5/0.5/" $gastask_conf
	sed -i "21s/\#0.25/0.25/" $gastask_conf
	sed -i "22s/\#0.125/0.125/" $gastask_conf

	sed -i "36s/1/\#1/" $gastask_conf

	echo "\n*dvfs\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
	'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
	mv task.txt $OUTPUT/task_$utilTarget+$networkUp+dvfs.txt


	sed -i "20s/0.5/\#0.5/" $gastask_conf
	sed -i "21s/0.25/\#0.25/" $gastask_conf
	sed -i "22s/0.125/\#0.125/" $gastask_conf
	echo "\n*nothing\n" >> $OUTPUT/output_$utilTarget+$networkUp.txt
	'./gastask' $gastask_conf >> $OUTPUT/output_$utilTarget+$networkUp.txt
	mv task.txt $OUTPUT/task_$utilTarget+$networkUp+nothing.txt

	sed -i "20s/\#0.5/0.5/" $gastask_conf
	sed -i "21s/\#0.25/0.25/" $gastask_conf
	sed -i "22s/\#0.125/0.125/" $gastask_conf
	sed -i "36s/\#1/1/" $gastask_conf
done

mv $gastask_conf $OUTPUT/gastask_$utilTarget+$$.conf
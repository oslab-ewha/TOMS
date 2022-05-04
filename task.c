#include "gastask.h"

unsigned	n_tasks;
task_t	tasks[MAX_TASKS];

unsigned	n_networks; // jennifer
network_t  networks[MAX_NETWORKS]; // jennifer

unsigned	n_net_commanders; // jennifer
net_commander_t  net_commanders[MAX_NETCOMMANDERS]; // jennifer

void
get_task_utilpower(unsigned no_task, unsigned char mem_type, unsigned char cloud_type, unsigned char cpufreq_type, unsigned char offloadingratio, unsigned char offloadingbool, double *putil, double *ppower_cpu, double *ppower_mem, double *ppower_net_com, double *pdeadline)
{
	task_t	*task = tasks + no_task;
	mem_t	*mem = mems + mem_type;
	cloud_t *cloud = clouds + cloud_type; // jennifer
	cpufreq_t	*cpufreq = cpufreqs + cpufreq_type;
	network_t	*network = networks + no_task; // jennifer
	net_commander_t   *net_commander = net_commanders + no_task; // jennifer
	double	wcet_scaled_cpu = 1 / cpufreq->wcet_scale;
	double	wcet_scaled_mem = 1 / mem->wcet_scale;
	double	wcet_scaled_cloud = 1 / cloud->computation_power; // jennifer
	double	cpu_power_unit;
	double  net_com_power_unit = 200; // jennifer
	double	wcet_scaled;
	double	transtime; // gyuri
	double  netcomtime; // jennifer
	wcet_scaled = task->wcet * wcet_scaled_cpu * wcet_scaled_mem; // ADDMEM
	// wcet_scaled = task->wcet * wcet_scaled_cpu; // jennifer
	
	if (wcet_scaled >= task->period)
		FATAL(3, "task[%u]: scaled wcet exceeds task period: %lf > %u", task->no, wcet_scaled, task->period);

	if (offloadingbool == 1) //gyuri
		offloadingratio = 0; //gyuri
	transtime = task->input_size/(double)network->uplink + task->output_size/(double)network->downlink; // gyuri // jennifer
	netcomtime = net_commander->intercept_out + net_commander->intercept_in;
	*putil = (wcet_scaled  * (1.0 - offloadingratios[offloadingratio]) + (wcet_scaled_cpu * netcomtime) * offloadingratios[offloadingratio]) / task->period; // gyuri
	*pdeadline = (wcet_scaled_cloud * task->wcet + wcet_scaled_cpu * netcomtime + transtime) / (task->period) * offloadingratios[offloadingratio]; //gyuri // jennifer
	cpu_power_unit = (cpufreq->power_active * wcet_scaled_cpu + cpufreq->power_idle * wcet_scaled_mem) / (wcet_scaled_cpu + wcet_scaled_mem);
	*ppower_cpu = cpu_power_unit * (wcet_scaled / task->period) * (1 - offloadingratios[offloadingratio]) + cpu_power_unit * (netcomtime / task->period) * (offloadingratios[offloadingratio]);// gyuri // jennifer
	*ppower_net_com = net_com_power_unit * (transtime / task->period) * offloadingratios[offloadingratio];  // jennifer
	*ppower_mem = task->memreq * (task->mem_active_ratio * mem->power_active + (1 - task->mem_active_ratio) * mem->power_idle) * wcet_scaled / task->period +
		task->memreq * mem->power_idle * (1 - wcet_scaled / task->period);  // not used
	//printf("cpu: %lf net_com: %lf mem: %lf\n", *ppower_cpu, *ppower_net_com, *ppower_mem);
	//printf("wcet_scaled: %lf, transtime: %lf, netcomtime: %lf\n", wcet_scaled, transtime, netcomtime); // jennifer delete
}

unsigned
get_task_memreq(unsigned no_task)
{
	task_t	*task = tasks + no_task;
	return task->memreq;
}

void
add_task(unsigned wcet, unsigned period, unsigned memreq, double mem_active_ratio, unsigned input_size, unsigned output_size)
{
	task_t	*task;

	task = tasks + n_tasks;
	task->wcet = wcet;
	task->period = period;
	task->memreq = memreq;
	task->mem_active_ratio = mem_active_ratio;
	task->input_size = input_size;
	task->output_size = output_size;

	n_tasks++;
	task->no = n_tasks;
}
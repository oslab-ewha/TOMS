#include "gastask.h"

unsigned	n_tasks;
task_t	tasks[MAX_TASKS];

unsigned	n_networks; 
network_t  networks[MAX_NETWORKS]; 

unsigned	n_net_commanders; 
net_commander_t  net_commanders[MAX_NETCOMMANDERS]; 

void
get_task_utilpower(unsigned no_task, unsigned char mem_type, unsigned char cloud_type, unsigned char cpufreq_type, unsigned char offloadingratio, double *putil, double *ppower_cpu, double *ppower_mem, double *ppower_net_com, double *pdeadline)
{
	task_t	*task = tasks + no_task;
	mem_t	*mem = mems + mem_type;
	cloud_t *cloud = clouds + cloud_type; 
	cpufreq_t	*cpufreq = cpufreqs + cpufreq_type;
	network_t	*network = networks + no_task; 
	net_commander_t   *net_commander = net_commanders + no_task; 
	double	wcet_scaled_cpu = 1 / cpufreq->wcet_scale;
	double	wcet_scaled_mem = 1 / mem->wcet_scale;
	double	wcet_scaled_cloud = 1 / cloud->computation_power; 
	double	cpu_power_unit;
	double  net_com_power_unit = 75; 
	double	wcet_scaled;
	double	transtime; 
	double  netcomtime; 
	wcet_scaled = task->wcet * wcet_scaled_cpu * wcet_scaled_mem; // ADDMEM
	// wcet_scaled = task->wcet * wcet_scaled_cpu; 
	
	if (wcet_scaled >= task->period)
		FATAL(3, "task[%u]: scaled wcet exceeds task period: %lf > %u", task->no, wcet_scaled, task->period);

	transtime = (task->task_size + task->input_size)/(double)network->uplink + task->output_size/(double)network->downlink;  
	netcomtime = net_commander->intercept_out + net_commander->intercept_in;
	*putil = (wcet_scaled  * (1.0 - offloadingratios[offloadingratio]) + (wcet_scaled_cpu * netcomtime) * offloadingratios[offloadingratio]) / task->period; 
	*pdeadline = (wcet_scaled_cloud * task->wcet + wcet_scaled_cpu * netcomtime + transtime) / (task->period) * offloadingratios[offloadingratio]; //gyuri 
	cpu_power_unit = (cpufreq->power_active * wcet_scaled_cpu + cpufreq->power_idle * wcet_scaled_mem) / (wcet_scaled_cpu + wcet_scaled_mem);
	*ppower_cpu = cpu_power_unit * (wcet_scaled / task->period) * (1 - offloadingratios[offloadingratio]) + cpu_power_unit * (netcomtime / task->period) * (offloadingratios[offloadingratio]); 
	*ppower_net_com = net_com_power_unit * ((transtime + netcomtime) / task->period) * offloadingratios[offloadingratio];  
	*ppower_mem = (task->memreq * (task->mem_active_ratio * mem->power_active + (1 - task->mem_active_ratio) * mem->power_idle) * wcet_scaled / task->period +
		task->memreq * mem->power_idle * (1 - wcet_scaled / task->period));
}

unsigned
get_task_memreq(unsigned no_task)
{
	task_t	*task = tasks + no_task;
	return task->memreq;
}

void
add_task(unsigned wcet, unsigned period, unsigned memreq, double mem_active_ratio, unsigned task_size, unsigned input_size, unsigned output_size, unsigned offloading_bool)
{
	task_t	*task;

	task = tasks + n_tasks;
	task->wcet = wcet;
	task->period = period;
	task->memreq = memreq;
	task->mem_active_ratio = mem_active_ratio;
	task->task_size = task_size;
	task->input_size = input_size;
	task->output_size = output_size;
	task->offloading_bool = offloading_bool;

	n_tasks++;
	task->no = n_tasks;
}

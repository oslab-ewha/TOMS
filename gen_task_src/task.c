/*
 * task.c
 * Manages the list of tasks and provides utility functions for task analysis in the TOMS system.
 *
 * Provides:
 *   - tasks: Array storing all task entries
 *   - n_tasks: Number of registered tasks
 *   - add_task(): Adds a new task with specified attributes
 *   - get_task_utilpower(): Calculates utilization and power consumption for a task under given resource assignments
 *   - get_task_utilpower_TEE(): Calculates utilization and power for a task considering Trusted Execution Environment (TEE) overheads
 *   - get_task_memreq(): Returns the memory requirement for a given task
 */

#include "gastask.h"

#define MBPS_TO_KBps   (1000.0 / 8.0)    // 1 Mbps = 125 KB/s
#define KBps_TO_KBms   (1.0 / 1000.0)    // KB/s → KB/ms
#define MBPS_TO_KBms   (MBPS_TO_KBps * KBps_TO_KBms)  // 최종 변환 (0.125)

unsigned	n_tasks;
task_t	tasks[MAX_TASKS];

extern unsigned	n_networks; 
extern network_t  networks[MAX_NETWORKS]; 

extern unsigned	n_net_commanders; 
extern net_commander_t  net_commanders[MAX_NETCOMMANDERS]; 

void
get_task_utilpower(unsigned no_task, unsigned char mem_type, unsigned char cloud_type, unsigned char cpufreq_type, unsigned char offloadingratio, double *putil, double *ppower_cpu, double *ppower_mem, double *ppower_net_com, double *pdeadline)
{
	task_t    *task = tasks + no_task;
	mem_t    *mem = mems + mem_type;
	cloud_t *cloud = clouds + cloud_type; 
	cpufreq_t    *cpufreq = cpufreqs + cpufreq_type;
	network_t    *network = networks + no_task; 
	net_commander_t   *net_commander = net_commanders + no_task; 
	double    wcet_scaled_cpu = 1 / cpufreq->wcet_scale;
	double    wcet_scaled_mem = 1 / mem->wcet_scale;
	double    wcet_scaled_cloud = 1 / cloud->computation_power; 
	double    cpu_power_unit;
	double  net_com_power_unit = 1; 
	double    wcet_scaled;
	double    transtime; 
	double  netcomtime; 

	// If any network uplink or downlink is 0, set all tasks' offloading_bool to 0
	if (network->uplink == 0.0 || network->downlink == 0.0) {
		for (unsigned i = 0; i < n_tasks; ++i) {
			tasks[i].offloading_bool = 0;
		}
	}

	wcet_scaled = task->wcet * wcet_scaled_cpu * wcet_scaled_mem; // ADDMEM
	// wcet_scaled = task->wcet * wcet_scaled_cpu; 
	
	// if (wcet_scaled >= task->period)
	//     FATAL(3, "task[%u]: scaled wcet exceeds task period: %lf > %u", task->no, wcet_scaled, task->period);
	if (network->uplink > 0.0 && network->downlink > 0.0) {
		transtime = ((task->task_size + task->input_size) / (double)network->uplink + task->output_size / (double)network->downlink) / MBPS_TO_KBms;
		netcomtime = net_commander->intercept_out + net_commander->intercept_in;
	}
	else{
		transtime = 0.0;
		netcomtime = 0.0;
	}
	
	*putil = (wcet_scaled  * (1.0 - offloadingratios[offloadingratio]) + (wcet_scaled_cpu * netcomtime) * offloadingratios[offloadingratio]) / task->period; 
	*pdeadline = (wcet_scaled_cloud * task->wcet + wcet_scaled_cpu * netcomtime + transtime) / (task->period) * offloadingratios[offloadingratio]; //gyuri 
	cpu_power_unit = (cpufreq->power_active * wcet_scaled_cpu + cpufreq->power_idle * wcet_scaled_mem) / (wcet_scaled_cpu + wcet_scaled_mem);
	*ppower_cpu = cpu_power_unit * (wcet_scaled / task->period) * (1 - offloadingratios[offloadingratio]) + cpu_power_unit * (netcomtime / task->period) * (offloadingratios[offloadingratio]); 
	*ppower_net_com = net_com_power_unit * ((transtime) / task->period) * offloadingratios[offloadingratio];  
	*ppower_mem = (task->memreq * (task->mem_active_ratio * mem->power_active + (1 - task->mem_active_ratio) * mem->power_idle) * wcet_scaled / task->period +
		task->memreq * mem->power_idle * (1 - wcet_scaled / task->period));
}

// TEE
void get_task_utilpower_TEE(unsigned no_task, unsigned char mem_type, unsigned char cloud_type, unsigned char cpufreq_type, unsigned char offloadingratio, double *putil, double *ppower_cpu, double *ppower_mem, double *ppower_net_com, double *pdeadline)
{
	task_t *task = tasks + no_task;
	mem_t *mem = mems + mem_type;
	cloud_t *cloud = clouds + cloud_type;
	cpufreq_t *cpufreq = cpufreqs + cpufreq_type;

	network_t *network = networks + no_task;
	net_commander_t *net_commander = net_commanders + no_task;
	double wcet_scaled_cpu = 1 / cpufreq->wcet_scale;
	double wcet_scaled_mem = 1 / mem->wcet_scale;
	double wcet_scaled_cloud = 1 / cloud->computation_power;
	double cpu_power_unit;
	double net_com_power_unit = 1;
	double wcet_scaled;
	double transtime;
	double netcomtime;

	// If any network uplink or downlink is 0, set all tasks' offloading_bool to 0
	if (network->uplink == 0.0 || network->downlink == 0.0) {
		for (unsigned i = 0; i < n_tasks; ++i) {
			tasks[i].offloading_bool = 0;
		}
	}

	wcet_scaled = task->wcet * wcet_scaled_cpu * wcet_scaled_mem;

	// TEE
	double IET, IDT, OET, ODT;
	double slowdown = 1.08;

	IET = task->input_size / 2000.0;
	IDT = IET;
	OET = task->output_size / 2000.0;
	ODT = OET;

	
	//if (wcet_scaled >= task->period)
	//    FATAL(3, "task[%u]: scaled wcet exceeds task period: %lf > %u", task->no, wcet_scaled, task->period);
	if (network->uplink > 0.0 && network->downlink > 0.0) {
		transtime = ((task->task_size + task->input_size) / (double)network->uplink + task->output_size / (double)network->downlink) / MBPS_TO_KBms;
		// TEE
		netcomtime = net_commander->intercept_out + net_commander->intercept_in + IET + ODT;
	}else{
		transtime = 0.0;
		netcomtime = 0.0;
	}
	*pdeadline = (wcet_scaled_cloud * task->wcet * ((1 - task->mem_active_ratio) + slowdown * task->mem_active_ratio) + wcet_scaled_cpu * netcomtime + transtime) / (task->period) * offloadingratios[offloadingratio]; // 1
	
	
	// Util for task
	*putil = (wcet_scaled * (1.0 - offloadingratios[offloadingratio]) + (wcet_scaled_cpu * netcomtime) * offloadingratios[offloadingratio]) / task->period;
	
	// Power Unit
	cpu_power_unit = (cpufreq->power_active * wcet_scaled_cpu + cpufreq->power_idle * wcet_scaled_mem) / (wcet_scaled_cpu + wcet_scaled_mem);
	
	// Power
	*ppower_cpu = cpu_power_unit * (wcet_scaled / task->period) * (1 - offloadingratios[offloadingratio]) 
				+ cpu_power_unit * (netcomtime / task->period) * (offloadingratios[offloadingratio]);

	*ppower_net_com = net_com_power_unit * ((transtime) / task->period) * offloadingratios[offloadingratio];
	
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
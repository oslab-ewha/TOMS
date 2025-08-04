#include "gasgen.h"

unsigned	wcet_min, wcet_max, mem_total;
double		util_cpu, util_target;
unsigned	n_tasks_target;
unsigned	task_size_min, task_size_max;
unsigned	input_size_min, input_size_max; 
unsigned	output_size_min, output_size_max; 
static double	util_sum_cpu, util_cpu_1task;
static unsigned	memreq_1task;
static unsigned	memreq_total;


static void gen_offloading_bool(unsigned *offloading_bool)
{
	int min_local = (int)((double)n_tasks_target/100 * 50);
	int locallist[min_local];
	
	for (int i = 0; i < min_local; i++)
	{
		locallist[i] = abs(rand()) % n_tasks_target;
		for (int j = 0; j < i; j++)
		{
			if (locallist[j] == locallist[i])
			{
				i--;
				break;
			}
		}
	}

	for (int i = 0; i < min_local; i++)
	{
		offloading_bool[locallist[i]] = 1;
	}
}

static void
do_gen_task(FILE *fp, int i, unsigned *offloading_bool)
{
	unsigned	wcet;
	unsigned	duration, memreq;
	double		mem_active_ratio;
	unsigned	task_size;
	unsigned    input_data_size, output_data_size; 

	wcet = wcet_min + get_rand(wcet_max - wcet_min + 1);
	duration = (unsigned)(wcet / util_cpu_1task);
	duration = duration + (int)get_rand(duration / 2) - (int)get_rand(duration / 2);

	memreq = memreq_1task + (int)get_rand(memreq_1task / 2) - (int)get_rand(memreq_1task / 2);
	mem_active_ratio = 0.1 + get_rand(1000) / 10000.0 - get_rand(1000) / 10000.0;

	task_size = task_size_min + get_rand(task_size_max - task_size_min + 1);
	input_data_size = input_size_min + get_rand(input_size_max - input_size_min + 1); 
	output_data_size = output_size_min + get_rand(output_size_max - output_size_min + 1); 

	util_sum_cpu += ((double)wcet / duration);
	memreq_total += memreq;

	fprintf(fp, "%u %u %u %lf %u %u %u %u\n", wcet, duration, memreq, mem_active_ratio, task_size, input_data_size, output_data_size, offloading_bool[i]); 
}

static double
get_mem_util(void)
{
	double	util_bymem = util_target - util_cpu;
	double	util_mem = 1.0 / n_mems;
	int	i;

	for (i = 1; i < n_mems && util_bymem > 0; i++) {
		double	util_overhead = 1 / mems[i].wcet_scale - 1;

		if (util_overhead < util_bymem) {
			util_bymem -= util_overhead;
			util_mem += 1.0 / n_mems;
		}
		else {
			util_mem += 1.0 / n_mems * util_bymem / util_overhead;
			break;
		}
	}

	return util_mem;
}

static double
get_util_overhead_bymem(unsigned mem_used)
{
	double	util_overhead = 0;
	unsigned	mem_total_per_type = mem_total / n_mems;
	int	i;

	for (i = 0; i < n_mems; i++) {
		double	overhead = 1 / mems[i].wcet_scale - 1;

		if (mem_used < mem_total_per_type) {
			util_overhead += overhead * mem_used / mem_total_per_type;
			break;
		}
		else {
			util_overhead += overhead;
			mem_used -= mem_total_per_type;
		}
	}

	return util_overhead;
}

void
gen_task(void)
{
	FILE	*fp;
	double	util_mem_1task;
	unsigned	i;
	unsigned	*offloading_bool;

	util_cpu_1task = util_cpu / n_tasks_target;
	util_mem_1task = get_mem_util() / n_tasks_target;
	memreq_1task = mem_total * util_mem_1task;

	fp = fopen("task_generated.txt", "w");
	if (fp == NULL) {
		FATAL(2, "cannot open task_generated.txt");
	}
	offloading_bool = (unsigned *)calloc(100, sizeof(unsigned));
	gen_offloading_bool(offloading_bool);
	
	for (i = 0; i < n_tasks_target; i++) {
		do_gen_task(fp, i, offloading_bool);
	}
	fclose(fp);

	printf("full power utilization: %lf\n", util_sum_cpu + get_util_overhead_bymem(memreq_total));
}

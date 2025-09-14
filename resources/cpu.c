/*
 * cpu.c
 * Implements CPU frequency resources for the system.
 * 
 * Defines and manages:
 *   - cpufreqs: array storing available CPU frequencies and their power characteristics
 *   - n_cpufreqs: number of registered CPU frequencies
 *   - add_cpufreq(): function to add a new CPU frequency with its properties
 */

#include "gastask.h"

cpufreq_t	cpufreqs[MAX_CPU_FREQS];
unsigned	n_cpufreqs;

void
add_cpufreq(double wcet_scale, double power_active, double power_idle)
{
	if (n_cpufreqs >= MAX_CPU_FREQS)
		FATAL(2, "too many cpu frequencies");

	if (n_cpufreqs > 0 && cpufreqs[n_cpufreqs - 1].wcet_scale < wcet_scale)
		FATAL(2, "cpu frequency should be defined in decreasing order");

	n_cpufreqs++;
	cpufreqs[n_cpufreqs - 1].wcet_scale = wcet_scale;
	cpufreqs[n_cpufreqs - 1].power_active = power_active;
	cpufreqs[n_cpufreqs - 1].power_idle = power_idle;
}

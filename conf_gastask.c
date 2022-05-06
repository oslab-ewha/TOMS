#include "gastask.h"

static void
parse_genetic(FILE *fp)
{
	char	buf[1024];

	while (fgets(buf, 1024, fp)) {
		if (buf[0] == '#')
			continue;
		if (buf[0] == '\n' || buf[0] == '*') {
			fseek(fp, -1 * strlen(buf), SEEK_CUR);
			return;
		}
		if (sscanf(buf, "%u %u %lf %lf", &max_gen, &n_pops, &cutoff, &penalty) != 4) {
			FATAL(2, "cannot load configuration: invalid genetic parameters: %s", trim(buf));
		}
	}
}

static void
parse_cpufreq(FILE *fp)
{
	char	buf[1024];

	while (fgets(buf, 1024, fp)) {
		double	wcet_scale, power_active, power_idle;

		if (buf[0] == '#')
			continue;
		if (buf[0] == '\n' || buf[0] == '*') {
			fseek(fp, -1 * strlen(buf), SEEK_CUR);
			return;
		}
		if (sscanf(buf, "%lf %lf %lf", &wcet_scale, &power_active, &power_idle) != 3) {
			FATAL(2, "cannot load configuration: invalid CPU frequency format: %s", trim(buf));
		}

		if (wcet_scale < 0 || wcet_scale > 1) {
			FATAL(2, "invalid cpu frequency wcet scale: %s", trim(buf));
		}
		if (power_active < 0 || power_idle < 0) {
			FATAL(2, "invalid cpu frequency power: %s", trim(buf));
		}
		add_cpufreq(wcet_scale, power_active, power_idle);
	}	
}

static void
parse_task(FILE *fp)
{
	char	buf[1024];

	while (fgets(buf, 1024, fp)) {
		unsigned	wcet, period, memreq;
		double		mem_active_ratio;
		unsigned	task_size;
		unsigned	input_size, output_size;
		unsigned	offloading_bool;

		if (buf[0] == '#')
			continue;
		if (buf[0] == '\n' || buf[0] == '*') {
			fseek(fp, -1 * strlen(buf), SEEK_CUR);
			return;
		}
		if (sscanf(buf, "%u %u %u %lf %u %u %u %u", &wcet, &period, &memreq, &mem_active_ratio, &task_size, &input_size, &output_size, &offloading_bool) != 8) {
			FATAL(2, "cannot load configuration: invalid task format: %s", trim(buf));
		}

		if (wcet >= period) {
			FATAL(2, "wcet is larger or equal than period: %s", trim(buf));
		}
		add_task(wcet, period, memreq, mem_active_ratio, task_size, input_size, output_size, offloading_bool);
	}
}

// jennifer
static void
parse_network(FILE *fp)
{
	char	buf[1024];

	while (fgets(buf, 1024, fp)) {
		unsigned	uplink, downlink;

		if (buf[0] == '#')
			continue;
		if (buf[0] == '\n' || buf[0] == '*') {
			fseek(fp, -1 * strlen(buf), SEEK_CUR);
			return;
		}
		if (sscanf(buf, "%u %u", &uplink, &downlink) != 2) {
			FATAL(2, "cannot load configuration: invalid network format: %s", trim(buf));
		}

		add_network(uplink, downlink);
	}
}

// jennifer
static void
parse_net_commander(FILE *fp)
{
	char	buf[1024];

	while (fgets(buf, 1024, fp)) {
		unsigned	intercept_out, intercept_in;

		if (buf[0] == '#')
			continue;
		if (buf[0] == '\n' || buf[0] == '*') {
			fseek(fp, -1 * strlen(buf), SEEK_CUR);
			return;
		}
		if (sscanf(buf, "%u %u", &intercept_out, &intercept_in) != 2) {
			FATAL(2, "cannot load configuration: invalid network commander format: %s", trim(buf));
		}

		add_net_commander(intercept_out, intercept_in);
	}
}

// jennifer
void
parse_cloud(FILE *fp)
{
	char	buf[1024];
	while (fgets(buf, 1024, fp)) {
		double	computation_power, power_active, power_idle, offloading_limit; // jennifer wcet
		unsigned max_capacity;
		char	type[1024];
		if (buf[0] == '#')
			continue;
		if (buf[0] == '\n' || buf[0] == '*') {
			fseek(fp, -1 * strlen(buf), SEEK_CUR);
			return;
		}
		if (sscanf(buf, "%s %lf %lf %lf %u %lf", type, &computation_power, &power_active, &power_idle, &max_capacity, &offloading_limit) != 6) {
			FATAL(2, "cannot load configuration: invalid cloud format: %s", trim(buf)); // jennifer wcet
		}
		if(max_capacity == 0){
			FATAL(2, "invalid max memory capacity: %s", trim(buf));
		}
		if (power_active < 0 || power_idle < 0) {
			FATAL(2, "invalid memory power: %s", trim(buf));
		}
		if (offloading_limit > 1){
			FATAL(2, "offloading limit is smaller or equal to one: %s", trim(buf));
		}
		add_cloud(type, computation_power, power_active, power_idle, max_capacity, offloading_limit); // jennifer wcet
	}
}

// jennifer
static void
parse_offloadingratio(FILE *fp)
{
	char	buf[1024];
	while (fgets(buf, 1024, fp)) {
		double	r;
		
		if (buf[0] == '#')
			continue;
		if (buf[0] == '\n' || buf[0] == '*') {
			fseek(fp, -1 * strlen(buf), SEEK_CUR);
			return;
		}
		if (sscanf(buf, "%lf", &r) != 1) {
			FATAL(2, "cannot load configuration: invalid ratio format: %s", trim(buf));
		}
		if (r < 0) {
			FATAL(2, "ratio should not be a negative value: %s", trim(buf));
		}

		if (r > 1) {
			FATAL(2, "ratio is smaller or equal to one: %s", trim(buf));
		}
		add_offloadingratio(r);
	}
}

void
parse_conf(FILE *fp)
{
	char	buf[1024];

	while (fgets(buf, 1024, fp)) {
		if (buf[0] == '\n' || buf[0] == '#')
			continue;
		switch (check_section(buf)) {
		case SECT_GENETIC:
			parse_genetic(fp);
			break;
		case SECT_GENTASK:
		case SECT_GENNETWORK: // jennifer
		case SECT_GENNETCOMMANDER: // jennifer
			skip_section(fp);
			break;
		case SECT_CPUFREQ:
			parse_cpufreq(fp);
			break;
		case SECT_MEM:
			parse_mem(fp);
			break;
		case SECT_TASK:
			if (n_cpufreqs == 0) {
				FATAL(2, "cpu frequency section should be defined ahead of task section");
			}
			parse_task(fp);
			break;
		case SECT_OFFLOADINGRATIO: // jennifer
			parse_offloadingratio(fp);
			break;
		case SECT_CLOUD:	// jennifer
			parse_cloud(fp);
			break;
		case SECT_NETWORK: // jennifer
			parse_network(fp);
			break;
		case SECT_NET_COMMANDER: // jennifer
			parse_net_commander(fp);
			break;
		default:
			errmsg("unknown section: %s", trim(buf));
			FATAL(2, "cannot load configuration");
		}
	}
}

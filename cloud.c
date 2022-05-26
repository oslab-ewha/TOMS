#include "gastask.h" 

cloud_t	clouds[MAX_CLOUDS];
unsigned	n_clouds;


void
add_cloud(const char *typestr, double computation_power, double power_active, double power_idle, unsigned max_capacity, double offloading_limit)
{
    cloud_t *cloud;

    if(n_clouds >= MAX_CLOUDS)
        FATAL(2, "too many cloud types");

    cloud = &clouds[n_clouds];
    cloud->typestr = strdup(typestr);
    cloud->computation_power = computation_power;
    cloud->power_active = power_active;
    cloud->power_idle = power_idle;
    cloud->max_capacity = max_capacity;
    cloud->offloading_limit = offloading_limit;
	n_clouds++;
}
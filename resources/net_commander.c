/*
 * net_commander.c
 * Manages the list of available net commander resources for the system.
 *
 * Provides:
 *   - net_commanders: Array storing net commander intercept values
 *   - n_net_commanders: Number of registered net commanders
 *   - add_net_commander(): Adds a new net commander with specified intercept values
 */

#include "gastask.h" 

net_commander_t	net_commanders[MAX_NETCOMMANDERS];
unsigned	n_net_commanders;

void
add_net_commander(unsigned intercept_out, unsigned intercept_in)
{
    net_commander_t *net_commander;
    net_commander = net_commanders + n_net_commanders;
    net_commander->intercept_out = intercept_out;
    net_commander->intercept_in = intercept_in;
	
	n_net_commanders++;
    net_commander->no = n_net_commanders;
}
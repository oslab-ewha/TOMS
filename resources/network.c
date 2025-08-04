/*
 * network.c
 * Manages the list of available network resources (uplink/downlink rates) for the system.
 *
 * Provides:
 *   - networks: Array storing network resource entries
 *   - n_networks: Number of registered networks
 *   - add_network(): Adds a new network resource with specified uplink and downlink rates
 */
#include "gastask.h" 

network_t	networks[MAX_NETWORKS];
unsigned	n_networks;

void
add_network(unsigned uplink, unsigned downlink)
{
    network_t *network;
    network = networks + n_networks;
    network->uplink = uplink;
    network->downlink = downlink;
	
	n_networks++;
    network->no = n_networks;
}
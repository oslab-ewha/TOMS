#include "gastask.h" // jennifer

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
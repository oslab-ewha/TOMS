/*
 * gen_network.c
 * Generates random network uplink and downlink values for the gasgen module.
 *
 * Provides:
 *   - do_gen_network(): Generates a single network entry with random uplink and downlink values within configured ranges and writes to file
 *   - gen_network(): Generates multiple network entries and writes them to "network_generated.txt"
 *   - Uses global configuration variables for uplink/downlink ranges and target count
 */

#include "gasgen.h" 

unsigned uplink_min, uplink_max, downlink_min, downlink_max;
unsigned n_networks_target;

static void
do_gen_network(FILE *fp)
{
    unsigned uplink, downlink;
    uplink = uplink_min + get_rand(uplink_max - uplink_min + 1);
    downlink = downlink_min + get_rand(downlink_max - downlink_min + 1);
    fprintf(fp, "%u %u\n", uplink, downlink);
}

void
gen_network(void)
{
    FILE    *fp;
    unsigned i;
    fp = fopen("network_generated.txt", "w");
    if(fp == NULL){
        FATAL(2, "cannot open network_generated.txt");
    }
    for(i=0; i < n_networks_target; i++){
        do_gen_network(fp);
    }
    fclose(fp);
}
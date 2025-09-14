/*
 * gen_netcommander.c
 * Generates random net commander intercept values for the gasgen module.
 *
 * Provides:
 *   - do_gen_net_commander(): Generates a single pair of intercept_out and intercept_in values within configured ranges and writes to file
 *   - gen_net_commander(): Generates multiple net commander entries and writes them to "network_commander_generated.txt"
 *   - Uses global configuration variables for intercept ranges and target count
 */

#include "gasgen.h" 

unsigned intercept_out_min, intercept_out_max, intercept_in_min, intercept_in_max;
unsigned n_net_commander_target;

static void
do_gen_net_commander(FILE *fp)
{
    unsigned intercept_out, intercept_in;
    intercept_out = intercept_out_min + get_rand(intercept_out_max - intercept_out_min + 1);
    intercept_in = intercept_in_min + get_rand(intercept_in_max - intercept_in_min + 1);
    fprintf(fp, "%u %u\n", intercept_out, intercept_in);
}

void
gen_net_commander(void)
{
    FILE    *fp;
    unsigned i;
    fp = fopen("network_commander_generated.txt", "w");
    if(fp == NULL){
        FATAL(2, "cannot open network_commander_generated.txt");
    }
    for(i=0; i < n_net_commander_target; i++){
        do_gen_net_commander(fp);
    }
    fclose(fp);
}
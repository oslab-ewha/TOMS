#include "gastask.h" 

double	offloadingratios[MAX_OFFLOADING_RATIOS];
unsigned	n_offloadingratios;

void
add_offloadingratio(double r)
{
    if(n_offloadingratios >= MAX_OFFLOADING_RATIOS)
        FATAL(2, "too many cloud ratios");

    if(n_offloadingratios > 0 && offloadingratios[n_offloadingratios - 1] > r)
        FATAL(2, "offloading ratio should be defined in increasing order");
	
	n_offloadingratios++;
    offloadingratios[n_offloadingratios - 1] = r;
}
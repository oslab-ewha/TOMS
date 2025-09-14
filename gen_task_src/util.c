/*
 * util.c
 * Utility functions for random number generation and related helpers.
 *
 * Provides:
 *   - get_rand(): Returns a random unsigned integer less than max_value
 *   - get_rand_except(): Returns a random unsigned integer less than max_value, except ex_value
 */
#include "common.h"

unsigned
get_rand(unsigned max_value)
{
	return abs(rand()) % max_value;
}

unsigned
get_rand_except(unsigned max_value, unsigned int ex_value)
{
	while (TRUE) {
		unsigned	value = get_rand(max_value);
		if (value != ex_value)
			return value;
	}
}

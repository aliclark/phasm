#!/bin/bash

# phasm.sh filename
#
# Fetch, compile and run the source code as a binary.
#
# This script can be used as a hash-bang interpreter.
#
# Any github files fetched will be cached for future under
# ~/cache/phasm/gh.

# TODO: give maps a proper parameter like '-m mapsfile'
#
# phasm.sh [-m mapsfile] [--] filename

# TODO: allow -s for 'script'
#
# phasm.sh [-m mapsfile] ([-c 'some script'] | [--] filename)

# TODO: cache output by both the input source and all Imports
# contained within, taking into account overlays.
#
# TODO: add -f flag to ignore binary cache, in case dependencies
# changed

phasmc_dir="$(dirname "$(readlink -f "$0")")"

input=$1
output=$(mktemp)

$phasmc_dir/phasmc.py <$input >$output
chmod +x $output

$output "$@"
status=$?

rm $output
exit $status

#!/bin/bash

# TODO: just do this in python and things will be easier..

script_name=$1

curdir="$(dirname "$(readlink -f "$0")")"
exe=$(mktemp)

#TODO: file: urls

if [[ $script_name == "gh:"* ]]; then
    # XXX: we *could* chmod +x the resulting script, since we know it should be
    # executable.
    echo "Import(\"$script_name\")" | $curdir/compiler.py >$exe
else
    $curdir/compiler.py <$script_name >$exe
fi
chmod +x $exe
$exe
status=$?

rm $exe
exit $status

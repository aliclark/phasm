#!/bin/sh

script=$1
exe=$(mktemp)
curdir="$(dirname "$(readlink -f "$0")")"
$curdir/compiler.py <$1 >$exe
chmod +x $exe

$exe
status=$?

rm $exe

exit $status

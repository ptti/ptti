#!/bin/bash

for regression in `find regression -type f -perm 0755`; do
	echo -n "${regression}... "
	if $regression > ${regression}.log 2>&1; then echo pass; else echo fail; fi
done

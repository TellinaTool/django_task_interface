#!/usr/bin/env bash

# usage: delete_filesystem.bash [name]
# This script deletes the virtual filesystem mounted at /name.
# This is meant to be run on the task interface host.

name=$1

# Exit on empty name
if [[ -z "${name// }" ]]; then
	exit 1
fi

set +e # ignore error from umount, if FS is already unmounted
umount -f /$name
set -e
rm -rf ~/$name.ext4
rm -rf /$name

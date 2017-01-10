#!/usr/bin/env bash

# usage: make_filesystem.bash [name]
# This script creates a virtual filesystem and mounts it at /name.
# It also copies the pre-defined filesystem in the data folder to /name/home/.
# This is meant to be run on the task interface host.

name=$1
fs_path=$2

# Exit on empty name
if [[ -z "${name// }" ]]; then
	exit 1
fi

mkdir /$name
dd if=/dev/zero of=~/$name.ext4 count=20480
mkfs.ext4 -q -F ~/$name.ext4
mount -o loop,rw ~/$name.ext4 /$name
mkdir /$name/home
# Copy file system
cp -r $fs_path /$name/home
chown --recursive vagrant:vagrant /$name/home

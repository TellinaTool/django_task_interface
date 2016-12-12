#!/usr/bin/env bash

name=$1

# Exit on empty name
if [[ -z "${name// }" ]]; then
	exit 1
fi

mkdir /$name
dd if=/dev/zero of=~/$name.ext4 count=20480 status=none
mkfs.ext4 -q -F ~/$name.ext4
mount -o loop,rw ~/$name.ext4 /$name
mkdir /$name/home
chown --recursive kvu:kvu /$name/home

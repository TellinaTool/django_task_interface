#!/usr/bin/env bash

name=$1

mkdir /$name
dd if=/dev/zero of=~/$name.ext4 count=20480 status=none
mkfs.ext4 -q -F ~/$name.ext4
mount -o loop,rw ~/$name.ext4 /$name
mkdir /$name/home
chown --recursive vagrant:vagrant /$name/home

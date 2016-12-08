#!/usr/bin/env bash

name=$1

umount -f /$name
rm -rf ~/$name.ext4
rm -rf /$name
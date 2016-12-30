#!/usr/bin/env bash

# This script will be run in the Vagrant VM (the guest) to set up tools needed
# to run the task interface server.

# Install curl.
sudo apt-get update
sudo apt-get install -y curl

# Install apparmor since I ran into this issue:
# https://github.com/docker/docker/issues/25488
sudo apt-get update
sudo apt-get install -y apparmor

# Install Docker.
curl -sSL https://get.docker.com/ | sh

# Allow Docker containers to ping host.
sudo iptables -A INPUT -i docker0 -j ACCEPT

# Install dependencies for building Python 3.
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev libbz2-dev libsqlite3-dev sqlite3

# Build Python 3.
cd /root
curl --silent -O 'https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tar.xz'
tar -xf Python-3.5.2.tar.xz
cd Python-3.5.2
./configure
make

# Install Python 3.
sudo make install

# Upgrade pip.
pip3 install --upgrade pip

#!/usr/bin/env bash

# This script will be run in the Vagrant VM (the guest) to set up tools needed
# to run the task interface server.

# Install docker
curl -sSL https://get.docker.com/ | sh

# Allow docker containers to ping host
sudo iptables -A INPUT -i docker0 -j ACCEPT

# Install pip3
sudo apt-get update
sudo apt-get install -y python3-pip
pip3 install --upgrade pip

# Install server dependencies
cd ~/tellina_task_interface/
sudo -H pip3 install -r requirements.txt

#!/usr/bin/env bash

# Install docker
curl -sSL https://get.docker.com/ | sh

# Allow docker containers to ping host
sudo iptables -A INPUT -i docker0 -j ACCEPT

# Install pip3
sudo apt-get update
sudo apt-get install -y python3-pip
pip3 install --upgrade pip

# Install emacs
sudo apt-get update
sudo apt-get install -y emacs

# Build the Docker image
cd ~/tellina_task_interface/docker_image
sudo docker build -t tellina .

# Install server dependencies
cd ~/tellina_task_interface/
sudo -H pip3 install -r requirements.txt

# Create database
rm -rf db.sqlite3 website/migrations
python3 manage.py makemigrations
python3 manage.py makemigrations website
python3 manage.py migrate

# Run server
sudo python3 manage.py runserver 0.0.0.0:10411

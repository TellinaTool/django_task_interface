# This file describes the operating system image that Vagrant will run.
# Start a VM by running `vagrant up` in the same directory as this file.

# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "bento/ubuntu-16.04"

  # Share the current folder with the VM
  config.vm.synced_folder "./", "/home/vagrant/tellina_task_interface"

  # The shell provisioner will run setup.bash after the OS is setup.
  config.vm.provision "shell", path: "setup.bash", privileged: false

  # Map the guest port to the host port so we can ping the server
  # inside the guest from the host.
  config.vm.network "forwarded_port", guest: 10411, host: 10411
end

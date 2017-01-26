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

  # Install required Vagrant plugins.
  required_plugins = %w( vagrant-reload vagrant-vbguest )
  required_plugins.each do |plugin|
    system "vagrant plugin install #{plugin}" unless Vagrant.has_plugin? plugin
  end

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  # config.vm.box = "hashicorp/precise64"
  config.vm.box = "ubuntu/xenial64"

  # Ensure that VirtualBox guest additions are reinstalled when the VM's
  # kernel is updated. We need guest additions for 'vagrant ssh'.
  config.vbguest.auto_update = true
  config.vbguest.no_remote = false

  # Upgrade the VM kernel to prepare for Docker install.
  # See https://docs.docker.com/engine/installation/linux/ubuntulinux/#/prerequisites-by-ubuntu-version.
  # config.vm.provision "shell", inline: <<-SHELL
  #   sudo apt-get update
  #   sudo apt-get install -y linux-image-generic-lts-trusty libgl1-mesa-glx-lts-trusty
  # SHELL

  # Reboot the VM so kernel upgrade works.
  config.vm.provision :reload

  # Share the current folder with the VM.
  config.vm.synced_folder "./", "/home/vagrant/tellina_task_interface"

  # The shell provisioner will run setup.bash after the OS is setup.
  config.vm.provision "shell", path: "vagrant_setup.bash"

  # Map the guest port to the host port so we can ping the server
  # inside the guest from the host.
  config.vm.network "forwarded_port", guest: 10411, host: 10411
  config.vm.network "forwarded_port", guest: 10412, host: 10412

  # Give more time for the VM to boot; default is 60 seconds.
  config.vm.boot_timeout = 300
end

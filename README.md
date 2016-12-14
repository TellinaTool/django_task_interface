# Tellina Task Interface

## Install dependencies

1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
2. Install [Vagrant](https://www.vagrantup.com/downloads.html).

## Run the server

1. Edit `config.json` as necessary.
2. Start the VM which runs the web application:

  ```bash
  cd tellina_task_interface
  vagrant destroy -f # destroy the existing VM, if any
  vagrant up
  ```

3. SSH into the VM and start the server:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make run
  ```

4. Start the task interface for user `bob` by visiting `http://127.0.0.1:10411/static/html/index.html?access_code=bob`.

5. Stop the server with `Ctrl-C`.

# Developing

1. Start the VM as shown above.
2. Edit files on the host. The repo folder on the host is synced with `/home/vagrant/tellina_task_interface` on the VM.
3. `vagrant ssh` into the VM and start the server again.

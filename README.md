# Tellina Task Interface

## Install dependencies

1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
2. Install [Vagrant](https://www.vagrantup.com/downloads.html).

## Run the server

Host will refer to the machine that runs `vagrant up`.
Guest will refer to the VM created by `vagrant up`.

1. Edit `config.json` as necessary.
2. Start the VM which runs the web application:

  ```bash
  cd tellina_task_interface
  vagrant destroy -f # destroy the existing VM, if any
  vagrant up
  ```

3. SSH into the guest and start the server:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make run
  ```

4. Start the task interface for user `bob` by visiting
   `http://127.0.0.1:10411/static/html/task.html` on a browser on the host.
   Enter `bob` in the browser prompt and continue.

5. Stop the server with `Ctrl-C` in the guest terminal.

6. View results in `~/tellina_task_interface/db.sqlite3` on the guest or host.

## Developing

If you edit `setup.bash`, which installs things on the guest, you'll need to
recreate the guest:

```bash
vagrant destroy -f
vagrant up
```

If you edit the Docker image in `docker_image/`, you'll need to rebuild the
image on the guest:

```bash
vagrant ssh
cd ~/tellina_task_interface/docker_image
sudo docker build -t tellina .
```

or recreate the VM:

```bash
vagrant destroy -f
vagrant up
```

If you edit files other than those mentioned above:

1. The repo folder on the host is synced with
   `/home/vagrant/tellina_task_interface` on the guest.
2. `vagrant ssh` into the guest and start the server again.

## Testing

1. Run automated tests and start the test server:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make test
  ```

2. Visit `http://127.0.0.1:10411/test`.
3. Verify that the page says "Tests passed".

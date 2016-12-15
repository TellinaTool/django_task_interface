# Tellina Task Interface (performance testing branch)

## Performance notes

* Disabled file locking, DB requests, and websocket messages from the container (see model.py and consumers.py)
* Server still chokes when I type too fast
* Conclusion: bottleneck is the rate of incoming websocket message from xterm

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

4. Start the task interface for user `bob` by visiting `http://127.0.0.1:10411/static/html/index.html?access_code=bob` on a browser on the host machine.

5. Stop the server with `Ctrl-C`.

6. View results in `~/tellina_task_interface/db.sqlite3`.

## Developing

If you edit `setup.bash`, which installs things on the VM, you'll need to recreate the VM:

```bash
vagrant destroy -f
vagrant up
```

If you edit the Docker image in `docker_image/`, you'll need to rebuild the image:

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

1. The repo folder on the host is synced with `/home/vagrant/tellina_task_interface` on the VM.
2. `vagrant ssh` into the VM and start the server again.

## Testing

1. Run automated tests and start the test server:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make test
  ```

2. Visit `http://127.0.0.1:10411/test`.
3. Verify that the page says "Tests passed".

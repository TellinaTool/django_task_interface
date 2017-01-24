# Tellina Task Interface

This repository contains experimental infrastructure for performing
a controlled experiment of people using the Tellina tool to create
and run bash commands.

## Install dependencies

1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
2. Install [Vagrant](https://www.vagrantup.com/downloads.html).

Command to do so for Ubuntu: `sudo apt-get install -y virtualbox vagrant`

## Create `config.json`

Run: `cp data/config.sample.json data/config.json`

The file `config.json` sets the task to be performed. 
To learn the format of the `config.json`, please refer to [this page](https://github.com/TellinaTool/tellina_task_interface/tree/master/data).

## Run the server

"Host" will refer to the machine that runs `vagrant up`.
"Guest" will refer to the VM created by `vagrant up`.

1. Edit `config.json` as necessary (see above).
2. Start the VM which runs the web application:

  ```bash
  cd tellina_task_interface
  vagrant destroy -f # destroy the existing VM, if any
  vagrant up
  ```
  Running the `vagrant` command may throw an error message if you're missing the required plug-ins. In this case, install them with the following commands:

  ```
  vagrant plugin install vagrant-reload
  vagrant plugin install vagrant-vbguest
  ```

3. SSH into the guest and start the server:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make run
  ```

5. Wait until you see `Quit the server with CONTROL-C.` in the console output.

6. Start the task interface for user `bob` by visiting
   `http://127.0.0.1:10411/static/html/task.html` in a browser on the host.
   Enter `bob` in the browser prompt and continue.

7. Stop the server with `Ctrl-C` in the guest terminal.

8. View results in `~/tellina_task_interface/db.sqlite3` on the guest or host.

## Developing

If you edit `setup.bash`, which installs things on the guest, you'll need to
recreate the guest:

```bash
vagrant destroy -f
vagrant up
```

If you edit other files:

1. The repo folder on the host is synced with
   `/home/vagrant/tellina_task_interface` on the guest.
2. `vagrant ssh` into the guest and start the server again.

Below is an overview of the implementation of the infrastructure.

### Architecture diagram

The task platform consists of four modules. The architecture is illustrated in the following diagram.

https://docs.google.com/drawings/d/1fwFaJsSLYY8wY7DZC0EBBdU_tgJDlwl9MVl5PLmIu0k

### I - Task Interface (Main) Server

The task interface server is implemented with Django. The core implementation can be found in [website/models.py](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py) and [website/views.py](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/views.py). It is connected to an SQLite database that stores the information of
* [user](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L30)
* [task](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L49)
* [container](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L72)
* [user study session](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L161)
* [task session](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L195)
* [user's action history](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L221)

The task interface server creates a "[user study session](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L161)" whenever a user starts a new task (initial login or task switch). A container that can be uniquely identified is [created](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/views.py#400) for a user study session. 

While a user is working on a task, the task interface server periodically [checks](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L409) if the task times out.

When the user executes a command, the difference between the current stdout/file system and the goal is [compared](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/views.py#L244). If the task is [completed] (https://github.com/TellinaTool/tellina_task_interface/blob/master/website/views.py#L247), the user is redirected to the next one.

(The Django configuration files are in the folder [tellina_task_interface/](https://github.com/TellinaTool/tellina_task_interface/tree/master/tellina_task_interface), which in general doesn't need to be changed.)

### II - Terminal (File System) Server

An ext4 file system with the name `{study_session_id}.ext4` is created for each study session. The file system is mounted to location `/{study_session_id}/` on the VM. The script used to create the file system on the VM can be found [here](https://github.com/TellinaTool/tellina_task_interface/blob/master/make_filesystem.bash).
The home directory `/{study_session_id}/home` on this physical location is [bound](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/models.py#L116) to path /home/study_participant/ in the docker container of that study session.

The docker container server is implemented with [Node.js](https://nodejs.org/en/). The core implementation can be found in [backend_container_image/app.js](https://github.com/TellinaTool/tellina_task_interface/blob/master/backend_container_image/app.js).

### III - WebSocket Proxy Server

The websocket proxy server is also implemented with Node.js. The core implementation can be found in [proxy_image/app.js](https://github.com/TellinaTool/tellina_task_interface/blob/master/proxy_image/app.js).

### IV - Front-end

The terminal is implemented with the third-party plugin [Xterm.js](https://github.com/TellinaTool/tellina_task_interface/tree/master/website/static/lib/xterm.js). The main custom implementation can be found [here](https://github.com/TellinaTool/tellina_task_interface/blob/master/website/static/js/task.js#L5).

The front-end periodically (every 0.5s) polls the task interface server for 
* if task status shows complete or time-out, proceed to the [next task](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/static/js/task.js#L20).

## Testing

1. Run automated tests:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make test
  ```

## Debugging

View `proxy.log` for a logs from the proxy server.

View `container_{container_id}.log` files for logs from backend containers.

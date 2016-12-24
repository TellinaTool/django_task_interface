# Tellina Task Interface

This repository contains experimental infrastructure for performing
a controlled experiment of people using the Tellina tool to create
and run bash commands.

## Architecture diagram

https://docs.google.com/drawings/d/1fwFaJsSLYY8wY7DZC0EBBdU_tgJDlwl9MVl5PLmIu0k

### Task Interface (Main) Server

The task interface server is implemented with Django. The core implementation can be found in [website/models.py](https://github.com/TellinaTool/tellina_task_interface/blob/2321d22147ad2226bc2fbdcfdc18e969794343ec/website/models.py). It is connected to an SQLite database that stores the information of
* [a user](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L459)
* [a task](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L114)
* [a task assignment](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L208), i.e. the match between a user and a container
* [a task result](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L154), i.e. if a user has successfully completed a task, how much time is spent, etc.

The task interface server creates a "[session](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L208)" whenever a user starts a new task (initial login or task switch). When a session is initialized, the user's container for previous task is [destroyed](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L296) and a new one is [created](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/models.py#L303). 

While a user is working on a task, the task interface server periodically [checks](https://github.com/TellinaTool/tellina_task_interface/blob/2321d22147ad2226bc2fbdcfdc18e969794343ec/website/models.py) if the task times out or has been completed.

(The Django configuration files are in the folder [tellina_task_interface/](https://github.com/TellinaTool/tellina_task_interface/tree/websocket_refactor/tellina_task_interface), which in general doesn't need to be changed.)

### Terminal (File System) Server

The docker container server is implemented with [Node.js](https://nodejs.org/en/). The core implementation can be found in [backend_container_image/app.js](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/backend_container_image/app.js).

### WebSocket Proxy Server

The websocket proxy server is also implemented with Node.js. The core implementation can be found in [proxy_image/app.js](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/proxy_image/app.js).

### Front-end

The terminal is implemented with the third-party plugin [Xterm.js](https://github.com/TellinaTool/tellina_task_interface/tree/websocket_refactor/website/static/lib/xterm.js). The main custom implementation can be found [here](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/static/js/task.js).

The front-end also periodically (every 0.5s) [polls] the task interface server for 
* [verifying if the task is completed or times out, if so, update task state] (https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/static/js/task.js#97)
* [most recent file system status] (https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/static/js/task.js#105)
* [if task status shows complete or time-out, proceed to the next task](https://github.com/TellinaTool/tellina_task_interface/blob/websocket_refactor/website/static/js/task.js#20).

## Install dependencies

1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
2. Install [Vagrant](https://www.vagrantup.com/downloads.html).

Command to do so for Ubuntu: `sudo apt-get install -y virtualbox vagrant`

## Create `config.json`

Run: `cp config.sample.json config.json`

The example file is for an experiment with the following setup,
but you can customize any of these aspects of the experiment:

* Each task takes 300 seconds.
* There are 2 participants: `bob` and `alice`.
* There are 2 tasks:
  1. Print hello world.
    * Initial filesystem: none
    * Answer: `hello world` is in standard output
  2. Create a file named `hello.txt` in `~/dir1/dir2`.
    * Initial file system:

       ```
       dir1/
       file.txt
         dir2/
       ```

    * Answer: user's home directory should look like

       ```
       dir1/
       file.txt
         dir2/
           hello.txt
       ```

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

## Testing

1. Run automated tests:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make test
  ```

## Debugging

Check `proxy.log` for a logs from the proxy server.

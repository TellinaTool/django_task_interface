# Tellina Task Interface

## Install dependencies

1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
2. Install [Vagrant](https://www.vagrantup.com/downloads.html).

## Create `config.json`

See `config.sample.json` for an example.

Given the following study setup:

* Each task takes 60 seconds.
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

The following JSON should be in `config.json`:

```json
{
  "access_codes": [
    "bob",
    "alice"
  ],
  "task_duration_in_seconds": 60,
  "tasks": [
    {
      "type": "stdout",
      "description": "Print hello world.",
      "initial_filesystem": {},
      "answer": "hello world"
    },
    {
      "type": "filesystem",
      "description": "Create a file named `hello.txt` in `~/dir1/dir2`.",
      "initial_filesystem": {
        "dir1": {
          "file.txt": null,
          "dir2": {}
        }
      },
      "answer": {
        "dir1": {
          "file.txt": null,
          "dir2": {
            "hello.txt": null
          }
        }
      }
    }
  ]
}
```

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

5. Wait until you see `INFO - server - Using busy-loop synchronous mode on channel layer` in the console output.

6. Start the task interface for user `bob` by visiting
   `http://127.0.0.1:10411/static/html/task.html` on a browser on the host.
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

1. Run automated tests and start the test server:

  ```bash
  vagrant ssh
  cd ~/tellina_task_interface
  make test
  ```

2. Visit `http://127.0.0.1:10411/test`.
3. Verify that the page says "Tests passed".

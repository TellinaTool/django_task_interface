# Tellina Task Interface

Edit `config.json` as necessary.

Start the VM which runs the web application:

```bash
cd tellina_task_interface
vagrant destroy -f # destroy the existing VM, if any
vagrant up
```

Start the task interface for user `bob` by visiting `http://127.0.0.1:10411/static/html/index.html?access_code=bob`.

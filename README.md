# Tellina Task Interface

Build the Docker image:

```bash
cd tellina_task_interface/docker_image
docker build -t tellina .
```

Run the web application:

```bash
cd tellina_task_interface
pip3 install -r requirements.txt
python3 manage.py runserver 0.0.0.0:10411
```

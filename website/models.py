from django.db import models
from channels import Channel

import docker
import requests
import os
import time
import subprocess

class Container(models.Model):
    '''
    STDIN channel: Channel(container.stdin_channel_name)
    STDIN transcript: container.stdin
    STDOUT transcript: container.stdout

    Message from the STDOUT channel are tagged as follows:
    message.channel_session['id'] = container_{container_id}
    '''

    container_id = models.TextField()
    stdin = models.TextField()
    stdout = models.TextField()

    # This is the name of the channel that sends STDIN to the container.
    stdin_channel_name = models.TextField()

    def write_stdin(self, text):
        while True:
            # Busy wait for stdin channel to be registered
            self.refresh_from_db()
            if self.stdin_channel_name != '':
                # Save STDIN to field
                self.stdin += text
                self.save()
                # Send STDIN on channel
                Channel(self.stdin_channel_name).send({'text': text})
                break
            os.sched_yield()

def create_filesystem(name):
    subprocess.run(['/bin/bash', 'make_filesystem.bash', name])

def create_docker_container(name):
    create_filesystem(name)
    cli = docker.Client(base_url='unix://var/run/docker.sock')
    container = cli.create_container(
        image='tellina',
        ports=[10411],
        volumes=['/home/myuser'],
        detach=True,
        host_config=cli.create_host_config(
            binds={
                '/{}/home'.format(name): {
                    'bind': '/home/myuser',
                    'mode': 'rw',
                },
            },
            port_bindings={10411: ('127.0.0.1',)},
        ),
    )
    container_id = container['Id']
    cli.start(container=container_id)
    info = cli.inspect_container(container_id)
    port = info['NetworkSettings']['Ports']['10411/tcp'][0]['HostPort']
    time.sleep(1)
    return (container_id, port)

def start_container(container_id):
    cli = docker.Client(base_url='unix://var/run/docker.sock')
    cli.start(container=container_id)

def create_container(name):
    # Race condition: Must create entry in DB before creating container,
    # so that websocket connect from container will be able to access that
    # entry in the DB.
    container_id, port = create_docker_container(name)
    container = Container.objects.create(container_id=container_id)
    start_container(container_id)

    r = requests.get('http://127.0.0.1:{}/{}'.format(port, container_id))
    return container

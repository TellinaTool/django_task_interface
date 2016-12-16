"""
This file defines handlers for WebSocket connect, message, and disconnect
events.

See https://channels.readthedocs.io/en/stable/getting-started.html#first-consumers
"""

from channels.sessions import channel_session, enforce_ordering
from .models import TaskManager
from channels import Channel

# Connected to websocket.connect
@enforce_ordering
@channel_session
def ws_connect(message):
    """
    This is called when a WebSocket connects to our server.

    This handler register the name of the Channel (which wraps the WebSocket)
    with the corresponding TaskManager.
    """

    # parse the URL path
    print('WS connect at: {}'.format(message.content['path']))
    path = message.content['path'].strip('/').split('/')

    # Handle /{type}/{task_manager_id}/{session_id}
    # This registers a xterm's or container's websocket with the corresponding task manager.
    if len(path) == 3:
        # Parse path into fields
        type = path[0]
        task_manager_id = path[1]
        session_id = path[2]

        # Set attributes that will be attached to every message from this websocket
        message.channel_session['type'] = type
        message.channel_session['task_manager_id'] = task_manager_id
        message.channel_session['session_id'] = session_id

        # Register this socket with the task manager
        task_manager = TaskManager.objects.get(id=task_manager_id)
        task_manager.lock()
        if session_id == task_manager.session_id:
            # Register if session_id matches
            if type == 'xterm':
                task_manager.xterm_stdout_channel_name = message.reply_channel.name
            elif type == 'container':
                task_manager.container_stdin_channel_name = message.reply_channel.name
            else:
                raise Exception('unrecognized websocket type')
            task_manager.save()
        else:
            # Ignore connection session_id does not match
            pass
        task_manager.unlock()

# Connected to websocket.receive
@enforce_ordering
@channel_session
def ws_message(message):
    """
    This is called when a message is sent to our server through a WebSocket
    connected to our server.

    This handler routes message from containers to xterms and from xterm to
    containers. It also appends message to the STDIN and STDOUT fields of the
    appropriate TaskManagers.
    """

    type = message.channel_session['type']
    task_manager_id = message.channel_session['task_manager_id']
    session_id = message.channel_session['session_id']
    text = message['text']

    print('WS message - type: {}, task_manager_id: {}, session_id: {}, text: {}'.format(type, task_manager_id, session_id, repr(text)))

    task_manager = TaskManager.objects.get(id=task_manager_id)
    task_manager.lock()
    if session_id == task_manager.session_id:
        # Get name of destination channel
        # Append to STDIN or STDOUT
        channel_name = None
        if type == 'xterm':
            channel_name = task_manager.container_stdin_channel_name
            task_manager.stdin += text
            task_manager.save()
        elif type == 'container':
            channel_name = task_manager.xterm_stdout_channel_name
            task_manager.stdout += text
            task_manager.save()
        else:
            raise Exception('unrecognized websocket type')

        # Forward to destination channel, if available
        if channel_name != '':
            Channel(channel_name).send({'text': text})
    task_manager.unlock()

# Connected to websocket.disconnect
@enforce_ordering
@channel_session
def ws_disconnect(message):
    """
    This is called when a WebSocket connected to our server disconnects.

    Currently, this handler does nothing.
    """

    pass

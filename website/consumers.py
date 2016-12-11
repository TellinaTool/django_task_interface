from channels.sessions import channel_session, enforce_ordering
from .models import Container

# Connected to websocket.connect
@enforce_ordering
@channel_session
def ws_connect(message):
    # parse the URL path
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

        # Attempt to register this socket with a task manager
        task_manager = TaskManager.objects.get(id=task_manager_id)
        task_manager.lock()
        if session_id == task_manager.session_id:
            if type == 'xterm':
                task_manager.xterm_stdout_channel_name = message.reply_channel.name
            elif type == 'container':
                task_manager.container_stdin_channel_name = message.reply_channel.name
            else:
                raise Exception('unrecognized websocket type')
            task_manager.save()
        task_manager.unlock()

# Connected to websocket.receive
@enforce_ordering
@channel_session
def ws_message(message):
    type = message.channel_session['type']
    task_manager_id = message.channel_session['task_manager_id']
    session_id = message.channel_session['session_id']

    # This ignores message that don't have a destination to send to
    task_manager = TaskManager.objects.get(id=task_manager_id)
    task_manager.lock()
    if session_id == task_manager.session_id:
        # send message
        channel_name = None
        if type == 'xterm':
            channel_name = task_manager.container_stdin_channel_name
        elif type == 'container':
            channel_name = task_manager.xterm_stdout_channel_name
        else:
            raise Exception('unrecognized websocket type')
        if channel_name != '':
            Channel(channel_name).send(message['text'])
    task_manager.unlock()

# Connected to websocket.disconnect
@enforce_ordering
@channel_session
def ws_disconnect(message):
    pass

from channels.sessions import channel_session, enforce_ordering
from .models import Container

# Connected to websocket.connect
@enforce_ordering
@channel_session
def ws_connect(message):
    # parse the URL path
    path = message.content['path'].strip('/').split('/')

    # Handle /container/{container_id}
    #
    # This registers a container's STDIN websocket connection with it's
    # corresponding model.
    if len(path) == 2 and path[0] == 'container':
        # Get container id
        container_id = path[1]

        # Update container model with STDIN channel name
        container = Container.objects.get(container_id=container_id)
        container.stdin_channel_name = message.reply_channel.name
        container.save()

        # Associate STDOUT messages with this container
        channel_id = 'container_{}'.format(container_id)
        message.channel_session['id'] = channel_id

# Connected to websocket.receive
@enforce_ordering
@channel_session
def ws_message(message):
    type, object_id = message.channel_session['id'].split('_')

    # Handle messages tagged with id = container_{container_id}.
    # Save these messages to the container's STDOUT field.
    if type == 'container':
        container = Container.objects.get(container_id=object_id)
        container.stdout += message['text']
        container.save()

# Connected to websocket.disconnect
@enforce_ordering
@channel_session
def ws_disconnect(message):
    pass

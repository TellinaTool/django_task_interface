from django.http import HttpResponse
from .models import *

import time

def test(request):
    # This should be a proper unit test in website/tests.py, but the container
    # cannot open a websocket to the test server started by the unit test, for
    # some unknown reason.
    container = create_container()
    time.sleep(2) # wait for container's websocket to connect to us
    container.refresh_from_db() # reload object from database
    print(container.stdout) # expect: this should print the initial terminal prompt
    container.write_stdin('ls\n') # send 'ls' command
    time.sleep(2) # wait for container to send STDOUT
    container.refresh_from_db()
    print(container.stdout) # expect: this should print the result of 'ls'

    return HttpResponse("Test done. Received following STDOUT: {}".format(container.stdout))

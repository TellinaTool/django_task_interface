$(document).ready(function () {
    // create terminal object
    var cols = 80;
    var rows = 40;
    var term = new Terminal({
        cursorBlink: true
    });
    var terminalContainer;
    var xtermWebSocket;

    // connect terminal to the study session's container
    $.get(`/get_container_port`, function(data) {
        console.log(data);
        var container_port = data.container_port;

        // connect to xterm
        terminalContainer = document.getElementById('terminal-container');
        // clean terminal
        while (terminalContainer.children.length > 0) {
            terminalContainer.removeChild(terminalContainer.children[0]);
        }
        // associate JS term object with HTML div
        term.open(terminalContainer);
        var charWidth = Math.ceil(term.element.offsetWidth / cols);
        var charHeight = Math.ceil(term.element.offsetHeight / rows);

        xtermWebSocket = new WebSocket(`ws:\/\/${location.hostname}:10412/${container_port}`);
        xtermWebSocket.onopen = function() {
            console.log('WebSocket opened');

            // Setup stdin and stdout buffers to collect and send streams to server
            var stdin = '';
            var stdout = '';

            // stdin from user input
            term.on('data', function(data) {
                xtermWebSocket.send(data);
                stdin += data;
            });

            // stdout from container
            xtermWebSocket.onmessage = function(event) {
                term.write(event.data);
                stdout += event.data;
            };

            /*
            // send stdin to server
            setInterval(function() {
                $.post(`/append_stdin?access_code=${accessCode}&session_id=${session_id}`, stdin,
                    function(data, textStatus, jqXHR) {
                        console.log(`append STDIN status ${jqXHR.status}`);
                    }
                );
                stdin = '';
            }, 500);
            // send stdout to server
            setInterval(function() {
                $.post(`/append_stdout?access_code=${accessCode}&session_id=${session_id}`, stdout,
                    function(data, textStatus, jqXHR) {
                        console.log(`append STDOUT status ${jqXHR.status}`);
                    }
                );
                stdout = '';
            }, 500); */
        };
        xtermWebSocket.onerror = function(event) {
            console.log('Socket error: ' + event.data);
        };
        xtermWebSocket.onclose = function() {
            console.log('Socket closed');
        };
    });

    $("#reset-button").click(function() {
        // reset file system
        $.get(`/reset_file_system`, function(data){
            console.log('Reset ' + data.container_id + ' file system.');
            term.clear();
        })
    });

    $("#quit-button").click(function() {
        $.get(`/go_to_next_task`, {reason: 'quit'}, function(data){
            if (data.status == 'STUDY_SESSION_COMPLETE') {
                BootstrapDialog.show({
                    title: "Study Completed",
                    message: "Congratulations, you have completed the study!",
                    buttons: [{
                        label: "Got it",
                        cssClass: "btn-primary",
                        action: function(dialogItself) {
                            dialogItself.close();
                        }
                    }]
                });
                console.log("Study session completed.");
            } else {
                // update database and reload task page
                window.location.replace(`http:\/\/${location.hostname}:10411/${data.task_session_id}`);
                console.log(`${location.hostname}:10411/${data.task_session_id}`);
            }
        });
    })
  }
);
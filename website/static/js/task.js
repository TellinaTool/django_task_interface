$(document).ready(
    $.get(`/get_container_port`, function(data) {
        console.log(data);
        var sessionID = data['session_id'];
        var container_port = data.container_port;
        console.log(`sessionID: ${sessionID}, port: ${port}`);

        // connect to xterm
        var cols = 80;
        var rows = 40;
        var term = new Terminal({
            cursorBlink: true
        });
        var terminalContainer = document.getElementById('terminal-container');
        // clean terminal
        while (terminalContainer.children.length > 0) {
            terminalContainer.removeChild(terminalContainer.children[0]);
        }
        // associate JS term object with HTML div
        term.open(terminalContainer);
        var charWidth = Math.ceil(term.element.offsetWidth / cols);
        var charHeight = Math.ceil(term.element.offsetHeight / rows);

        var xtermWebSocket = new WebSocket(`ws://${location.hostname}:10412/${port}`);
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
                $.post(`/append_stdin?access_code=${accessCode}&session_id=${sessionID}`, stdin,
                    function(data, textStatus, jqXHR) {
                        console.log(`append STDIN status ${jqXHR.status}`);
                    }
                );
                stdin = '';
            }, 500);
            // send stdout to server
            setInterval(function() {
                $.post(`/append_stdout?access_code=${accessCode}&session_id=${sessionID}`, stdout,
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
);
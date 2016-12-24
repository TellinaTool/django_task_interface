var accessCode = prompt("Enter your access code");

// get the current task ID
$.get(`/get_current_task_id?access_code=${accessCode}`, function(data) {
    var task_id = parseInt(data);
    console.log(`task_id: ${task_id}`);

    // get details about the current task
    $.get(`/get_task?task_id=${task_id}`, function(data) {
        var task = data;
        console.log(`task: ${JSON.stringify(task)}`);
    });

    alert(`You are starting a session for task ${task_id}. Press OK to continue.`);

    // initialize a sesion for the current task
    $.get(`/initialize_task?access_code=${accessCode}&task_id=${task_id}`, function(data) {

        // poll task state
        setInterval(function() {
            $.get(`/check_task_state?access_code=${accessCode}&task_id=${task_id}`, function(data) {
                var state = data;
                console.log(`task state: ${state}`);
                if (state !== 'running') {
                    location.reload();
                }
            });
        }, 500);

        console.log(data);
        var sessionID = data['session_id'];
        var port = data['port'];
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
            }, 500);
        };
        xtermWebSocket.onerror = function(event) {
            console.log('Socket error: ' + event.data);
        };
        xtermWebSocket.onclose = function() {
            console.log('Socket closed');
        };

        // poll update for debugging purpose
        setInterval(function() {
            $.get(`/update_state?access_code=${accessCode}`, function(data) {
                console.log(`updated`);
            });
        }, 500);

        // poll filesystem for debugging purpose
        setInterval(function() {
            $.get(`/get_filesystem?access_code=${accessCode}`, function(data) {
                var filesystem = data;
                console.log(`filesystem: ${JSON.stringify(filesystem)}`);
            });
        }, 500);
    });
});
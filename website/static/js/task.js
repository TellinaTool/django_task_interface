$(document).ready(function () {
    // restore the $.browser method of jQuery<1.9
    jQuery.browser = {};
    (function () {
        jQuery.browser.msie = false;
        jQuery.browser.version = 0;
        if (navigator.userAgent.match(/MSIE ([0-9]+)\./)) {
            jQuery.browser.msie = true;
            jQuery.browser.version = RegExp.$1;
        }
    })();

    var task_time_out;
    // create terminal object
    var term, protocol, socketURL, socket, pid, charWidth, charHeight;
    var terminalContainer = document.getElementById('bash-terminal');

    var filesystem_error_msg = "We've caught a file system error in the backend. Please try a few seconds later."

    create_new_terminal();

    // connect xterm.js terminal to the study session's container
    $.get(`/get_additional_task_info`, function(data) {
        status = data.filesystem_status;
        if (status != "FILE_SYSTEM_WRITTEN_TO_DISK")
            alert(filesystem_error_msg);

        var container_port = data.container_port;

        set_websocket(container_port);

        refresh_vis(data);

        // start timing the task
        task_time_out = setTimeout(function() {
             console.log('task time out');
             clearTimeout(task_time_out);

             // prompt the user that they have to move on to the next task
             BootstrapDialog.show({
                 title: "Time's Up",
                 message: "The current task session is time out. Please proceed to the next task.",
                 buttons: [{
                     label: "Proceed",
                     cssClass: "btn-primary",
                     action: function(dialogItself) {
                         dialogItself.close();
                         switch_task('time_out');
                     }
                 }],
                 closable: false,
             });
        }, data.task_duration * 1000);

        $("#reset-button").click(function() {
            // close the websocket connection to the old container
            socket.close();
            create_new_terminal();
            // reset file system
            $.get(`/reset_file_system`, function(data){
                status = data.filesystem_status;
                if (status == 'FILE_SYSTEM_ERROR')
                    alert(filesystem_error_msg);
                console.log(data.container_port);
                // open websocket connection to the new container
                set_websocket(data.container_port);
                refresh_vis(data);
            })
        });

        $("#quit-button").click(function() {
            // discourage a user from quiting a task
            BootstrapDialog.show({
                title: "We hope everyone try harder before giving up a task!",
                message: "If you give up a task, the information we get from the study wil be less accurate. Would you like to proceed anyway?",
                type: BootstrapDialog.TYPE_WARNING,
                buttons: [
                {
                    icon: 'glyphicon glyphicon-warning-sign',
                    label: " Yes, give up.",
                    cssClass: "btn-danger",
                    action: function(dialogItself) {
                        dialogItself.close();
                        switch_task('quit');
                    }
                },
                {
                    label: "No, I'll keep trying",
                    cssClass: "btn-primary",
                    action: function(dialogItself) {
                        dialogItself.close();
                    }
                }],
            });
        })
    });

    function refresh_vis(data) {
        if (data.hasOwnProperty('stdout_diff')) {
            console.log(data);
            // reset height of file system diff and stdout diff
            $("#stdout-diff-vis-container").show();
            $("#current-tree-vis-container").css('bottom', '50%');
            build_stdout_vis(data.stdout_diff, "#stdout-diff-vis");
        }
        // file system diff visualization
        build_fs_tree_vis(data.filesystem_diff, "#current-tree-vis");
        console.log(data.filesystem_diff);
    }

    function set_websocket(container_port)  {
        protocol = (location.protocol === 'https:') ? 'wss://' : 'ws://';
        socketURL = protocol + location.hostname + `:10412/${container_port}`;

        /* var initialGeometry = term.proposeGeometry(),
          cols = initialGeometry.cols,
          rows = initialGeometry.rows;
        term.resize(cols, rows);
        charWidth = Math.ceil(term.element.offsetWidth / cols);
        charHeight = Math.ceil(term.element.offsetHeight / rows); */

        socket = new WebSocket(socketURL);
        socket.onopen = function() {
            console.log('WebSocket opened');

            // runFakeTerminal();
            runRealTerminal();

            // Setup stdin and stdout buffers to collect and send streams to server
            var stdin = '';
            var stdout = '';

            // stdin from user input
            term.on('data', function(data) {
                stdin += data;
            });

            // stdout from container
            socket.onmessage = function(event) {
                // term.write(event.data);
                stdout += event.data;
                // send the standard output to the backend whenever the user executes a command
                // in the terminal
                if (stdout.match(/(.|\n)*me\@[0-9a-z]{12}\:[^\n]*\$ $/)) {
                    if (stdout.split('\n').length > 1) {
                        $.post(`/on_command_execution`, {stdout: stdout},
                            function(data) {
                                refresh_vis(data);
                                if (data.status == 'TASK_COMPLETED') {
                                    clearTimeout(task_time_out);
                                    setTimeout(function() {
                                        BootstrapDialog.show({
                                            title: "Great Job!",
                                            message: "You passed the task! Please proceed to the next task.",
                                            buttons: [{
                                                label: "Proceed",
                                                cssClass: "btn-primary",
                                                action: function(dialogItself) {
                                                    dialogItself.close();
                                                    switch_task('passed');
                                                }
                                            }],
                                            closable: false
                                        });
                                    }, 300);
                                }
                            }
                        );
                    }
                    console.log(JSON.stringify(stdout));
                    stdout = '';
                }
            };
        }
        socket.onerror = function(event) {
            console.log('Socket error: ' + event.data);
        };
        socket.onclose = function() {
            console.log('Socket closed');
        };
    }

    /* $(".accordion").scroll(function(event) {
        $(".accordion-section-heading").css("position", "fixed");
    }); */

    function runRealTerminal() {
        term.attach(socket);
        term._initialized = true;
    }

    function switch_task(reason) {
        $("button").attr("disabled", "disabled");
        $("#wait-dialog").modalDialog();
        // close the websocket connection to the current container
        socket.close();
        $.get(`/go_to_next_task`, {reason_for_close: reason}, function(data){
            if (data.status == 'STUDY_SESSION_COMPLETE') {
                BootstrapDialog.show({
                    title: "Congratulations, you have completed the study!",
                    message: "Report: passed " + data.num_passed + "/" + data.num_total + " tasks; given up " + data.num_given_up + "/" + data.num_total + " tasks.\n\n" +
                             "Please go on to fill in the post-study questionnaire.",
                    buttons: [{
                        label: "Go to questionnaire",
                        cssClass: "btn-primary",
                        action: function(dialogItself) {
                            dialogItself.close();
                            setTimeout(window.location.replace(`http:\/\/${location.hostname}:10411`), 2000);
                        }
                    }],
                    closable: false,
                });
                console.log("Study session completed.");
            } else {
                window.location.replace(`http:\/\/${location.hostname}:10411/${data.task_session_id}`);
                console.log(`${location.hostname}:10411/${data.task_session_id}`);
            }
        });
    }

    function create_new_terminal() {
        term = new Terminal({
            cursorBlink: true
        });
        // clean terminal container
        while (terminalContainer.children.length > 0) {
            terminalContainer.removeChild(terminalContainer.children[0]);
        }
        // associate JS term object with HTML div
        term.open(terminalContainer);
        term.fit();
        // console.log(term.cols);
        // console.log(term.rows);
    }
});

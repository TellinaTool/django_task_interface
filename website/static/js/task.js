$(document).ready(function () {
    // create terminal object
    // var cols = 80;
    // var rows = 40;
    var term = new Terminal({
        cursorBlink: true
    });

    var terminalContainer = document.getElementById('bash-terminal');
    // clean terminal container
    while (terminalContainer.children.length > 0) {
        terminalContainer.removeChild(terminalContainer.children[0]);
    }
    // associate JS term object with HTML div
    term.open(terminalContainer);
    // var charWidth = Math.ceil(term.element.offsetWidth / cols);
    // var charHeight = Math.ceil(term.element.offsetHeight / rows);

    term.fit();

    /* $('#bash-terminal').resize(function() {
        term.fit();
    }); */

    // connect xterm.js terminal to the study session's container
    $.get(`/get_container_port`, function(data) {
        var container_port = data.container_port;
        var task_time_out;

        var xtermWebSocket = new WebSocket(`ws:\/\/${location.hostname}:10412/${container_port}`);
        xtermWebSocket.onopen = function() {
            console.log('WebSocket opened');

            // Setup stdin and stdout buffers to collect and send streams to server
            var stdin = '';
            var stdout = '';

            // stdin from user input
            term.on('data', function(data) {
                // console.log(data);
                xtermWebSocket.send(data);
                stdin += data;
            });

            // stdout from container
            xtermWebSocket.onmessage = function(event) {
                term.write(event.data);
                stdout += event.data;
                // send the standard output to the backend whenever the user executes a command
                // in the terminal
                if (stdout.match(/(.|\n)*\nme\@[0-9a-z]+\:[^\n]*\$ $/)) {
                    if (stdout.split('\n').length > 1) {
                        $.post(`/on_command_execution`, {stdout: stdout},
                            function(data) {
                                console.log(data.filesystem_diff);
                                current_tree_vis = data.filesystem_diff;
                                current_tree_vis.name = '/';
                                console.log(current_tree_vis);
                                build_fs_tree_vis(current_tree_vis, "#current-tree-vis");
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
                    console.log(stdout);
                    stdout = '';
                }
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
            */
        };

        xtermWebSocket.onerror = function(event) {
            console.log('Socket error: ' + event.data);
        };
        xtermWebSocket.onclose = function() {
            console.log('Socket closed');
        };

        // start timing the task
        $.get(`/get_task_duration`, function(data) {
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
            }, parseInt(data.duration) * 10000);

            // initial directory visualization
            current_tree_vis = data.current_filesystem;
            current_tree_vis.name = '/';
            build_fs_tree_vis(current_tree_vis, "#current-tree-vis");
            build_fs_tree_vis(data.goal_filesystem, "#goal-tree-vis");
        });

        $("#reset-button").click(function() {
            // reset file system
            $.get(`/reset_file_system`, function(data){
                console.log('Reset ' + data.container_id + ' file system: ' + data.filesystem_status);
                current_tree_vis = data.current_filesystem;
                current_tree_vis.name = '/';
                build_fs_tree_vis(current_tree_vis, "#current-tree-vis");
                term.clear();
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

        function switch_task(reason) {
            $("button").attr("disabled", "disabled");
            $.get(`/go_to_next_task`, {reason_for_close: reason}, function(data){
                if (data.status == 'STUDY_SESSION_COMPLETE') {
                    // print "thank you" message in the terminal
                    /* term.write("\n");
                    term.write("    .▀█▀.█▄█.█▀█.█▄.█.█▄▀　█▄█.█▀█.█─█\n");
                    term.write("    ─.█.─█▀█.█▀█.█.▀█.█▀▄　─█.─█▄█.█▄█\n");
                    */
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
                    // update database and reload task page
                    window.location.replace(`http:\/\/${location.hostname}:10411/${data.task_session_id}`);
                    console.log(`${location.hostname}:10411/${data.task_session_id}`);
                }
            });
        }
    });
});

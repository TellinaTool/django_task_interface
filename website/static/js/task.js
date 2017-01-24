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

    var is_training = false;
    var showing_tips = false;
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

        // Check if page tour needs to be displayed
        console.log(data.page_tour);
        if (data.page_tour == 'init_filesystem_change' ||
            data.page_tour == 'init_file_search' ||
            data.page_tour == 'init_standard_output')  {
            // start training tutorial
            var intro = introJs();
            intro.setOptions({
                steps: [
                    {
                        element: "#img-overlay-hanger",
                        intro: "<p>Welcome to the task platform training!</p><p>The three main components of the task platform is illustrated below.</p><img src=\"static/img/task_platform.png\" height=\"100%\" width=\"100%\"></img><br>",
                    }
                ]
            }).setOption("tooltipClass", "img-overlay")
            .setOption('showStepNumbers', false)
            .setOption('exitOnOverlayClick', false)
            .setOption('showBullets', false)
            .start();
        }

        // start timing the task
        if (!is_training && !showing_tips) {
            start_timer(data.task_duration);
        }

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
            if (is_training) {
                // reveal the answer to the user if he/she decides to quit the
                // training tasks
                BootstrapDialog.show({
                    title: "Solution",
                    message: "The solution to this task is \"find css -type f\". Input this command in the terminal and observe the effect.",
                    buttons: [
                    {
                        label: "Got it.",
                        cssClass: "btn-danger",
                        action: function(dialogItself) {
                            dialogItself.close();
                        }
                    }]
                });
            } else {
                // discourage a user from quiting a task
                BootstrapDialog.show({
                    title: "Warning",
                    message: "Do you really want to give up on this task?",
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
            }
        })
    });

    function start_timer(num_secs) {
        console.log('timer starts');
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
        }, num_secs * 1000);
    }

    function refresh_vis(data) {
        // file system diff visualization
        
        $("#task-progress-vis").empty();
        $("#task-progress-vis").append('<div style="font-weight: bold;">You still have something more to work on...</div>');
        $("#task-progress-vis").append("<ol id='task-progress-report'></ol>");

        build_fs_tree_vis(data.filesystem_diff, "#current-tree-vis");
        $("#task-progress-report").append('<li><font style="text-decoration: underline;">Your current filesystem status does not match the goal file system status \
                                            (view the visualization above for details).</font>\
                                                <ul class="legend-ul"><li>Files/Directories that are <b>extra</b> in your FS: \
                                                    <span style="color:red; text-decoration: line-through;"><span class="glyphicon glyphicon-file"></span>file</span> or \
                                                    <span style="color:red; text-decoration: line-through;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.</li>\
                                                <li>Files/Directories <b>missing</b> in your current FS: \
                                                    <span style="opacity: 0.3;"><span class="glyphicon glyphicon-file"></span>file</span> or \
                                                    <span style="opacity: 0.3;"><span class="glyphicon glyphicon-folder-close"></span>dir</span></li>\
                                                </ul></li>');

        $("#task-progress-report").append('<li><font style="text-decoration: underline;">Files/directories selected by your command mismatches the desirable result \
                                                    (view the file system visualization for details)</font>:\
                                            <ul class="legend-ul"><li>Files/Directories your command <b>failed</b> to select: \
                                                    <span style="background-color: #CCCCCC;"><span class="glyphicon glyphicon-file"></span>file</span>,\
                                                    <span style="background-color: #CCCCCC;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.</li>\
                                                <li>Files/Directories your command <b>wrongly</b> selected: \
                                                    <span style="background-color: #DF9496;"><span class="glyphicon glyphicon-file"></span>file</span>,\
                                                    <span style="background-color: #DF9496;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.</li>\
                                                <li>Files/Directories your command <b>correctly</b> selected: \
                                                    <span style="background-color: #FEFCD7;"><span class="glyphicon glyphicon-file"></span>file</span>,\
                                                    <span style="background-color: #FEFCD7;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.</li>\
                                                </ul></li>');

        if (data.hasOwnProperty('stdout_diff')) {
            //console.log(data);
            // reset height of file system diff and stdout diff
            //$("#task-progress-container").show();
            //$("#current-tree-vis-container").css('bottom', '50%');
            $("#task-progress-report").append('<li><font style="text-decoration: underline;">Your terminal output mismatches the solution output, see below</font>: \
                                                   <ul class="legend-ul"><li>There are lines missing in your print result: <span style="color:#CCCCCC">an output line</span>.</li> \
                                                    <li>There are lines wrongly printed by your command: <span style="color: red;text-decoration:line-through">an output line</span>.</li></ul>\
                                                    <div id="std-out-diff" style="min-height:10px;border-style: dashed; padding-left:10px;"></div>\
                                              </li>');
            build_stdout_vis(data.stdout_diff, "#std-out-diff");

        }

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
                                    if (is_training) {
                                        var calloutMgr = hopscotch.getCalloutManager();
                                        calloutMgr.createCallout({
                                          id: 'attach-icon',
                                          target: 'current-tree-vis',
                                          placement: 'left',
                                          title: 'Task Completed',
                                          content: 'When you print the correct files on the terminal, there will be no difference mark ups on the visualization.',
                                          onClose: function() {
                                            setTimeout(function() {
                                                BootstrapDialog.show({
                                                    title: "Training Completed",
                                                    message: "Awesome! You've completed the task platform training. You are ready to start the user study session.",
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
                                            }, 300)
                                          }
                                        });
                                     } else {
                                        setTimeout(function() {
                                            BootstrapDialog.show({
                                                title: "Good Job",
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
        //$("#wait-dialog").css('visibility','visible');
        //$("#wait-dialog").modalDialog();
        var $waitmsg = $('<div style="font-size:12pt;text-align: center">Please wait while we are setting up the next task...</div>');
        $waitmsg.append('<br />');
        $waitmsg.append('<img src="static/img/hourglass.gif" />');

        BootstrapDialog.show({
            title: "Please wait...",
            message: $waitmsg,
            closable: false
        });

        // close the websocket connection to the current container
        socket.close();
        $.get(`/go_to_next_task`, {reason_for_close: reason}, function(data){
            if (data.status == 'STUDY_SESSION_COMPLETE') {
                BootstrapDialog.show({
                    title: "Congratulations, you have completed the study!",
                    message: "Report: passed " + data.num_passed + "/" + data.num_total +
                             " tasks; given up " + data.num_given_up + "/" + data.num_total + " tasks.\n\n" +
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
                // window.location.replace('progress');
            } else {
                if (data.status == 'SWITCH_PART') {
                    window.location.replace('progress');
                } else {
                    window.location.replace(`http:\/\/${location.hostname}:10411/${data.task_session_id}`);
                    console.log(`${location.hostname}:10411/${data.task_session_id}`);
                }
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

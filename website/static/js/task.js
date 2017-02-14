$(document).ready(function () {
    // restore the $.browser method for jQuery<1.9
    jQuery.browser = {};
    (function () {
        jQuery.browser.msie = false;
        jQuery.browser.version = 0;
        if (navigator.userAgent.match(/MSIE ([0-9]+)\./)) {
            jQuery.browser.msie = true;
            jQuery.browser.version = RegExp.$1;
        }
    })();

    var normal_exit = false;
    // prevent user from refreshing the page
    window.onbeforeunload = function() {
        if (!normal_exit) {
            // $.get(`/task_session_pause`);
            return "Your task session has not been completed, are you sure you want to leave?";
        }
    }

    var is_training = false;
    var is_first_training = false;
    var is_second_training = false;
    var task_time_out;

    // create terminal object
    var term, protocol, socketURL, socket, pid, charWidth, charHeight;
    var terminalContainer = document.getElementById('bash-terminal');

    create_new_terminal();

    // connect xterm.js terminal to the study session's container
    $.get(`/get_additional_task_info`, function(data) {
        status = data.filesystem_status;
        if (status != "FILE_SYSTEM_WRITTEN_TO_DISK") {
            // TODO: a file system error is likely to be caused by a
            // container or proxy server failure. The webpage needs to
            // keep running when this happens, therefore do nothing.
            console.log(filesystem_error_msg);
        }

        var container_port = data.container_port;

        set_websocket(container_port);

        refresh_vis(data);

        // check if stage change & training information needs to be displayed
        if (data.status == 'ENTERING_STAGE_I') { 
            is_training = true;
            is_first_training = true;
            start_task_platform_training(data);
         } else if (data.status == 'ENTERING_STAGE_II') { 
            is_training = true;
            is_second_training = true;
            show_training_task_ii_assistant_tool_dialog(data);
         }

        // start timing the task
        if (!is_training) {
            start_timer();
        }

        $("#reset-button").click(function() {
            // close the websocket connection to the old container
            socket.close();
            create_new_terminal();
            // reset file system
            $.get(`/reset_file_system`, function(data){
                status = data.filesystem_status;
                if (status == 'FILE_SYSTEM_ERROR') {
                    // TODO: a file system error is likely to be caused by a
                    // container or proxy server failure. The webpage needs to
                    // keep running when this happens, therefore do nothing.
                    // alert(filesystem_error_msg);
                    console.log(filesystem_error_msg);
                }
                console.log(data.container_port);
                // open websocket connection to the new container
                set_websocket(data.container_port);
                refresh_vis(data);
            })
        });

        $("#quit-button").click(function() {
            if (is_training) {
                show_solution_dialog(data.task_solution);
            } else {
                show_quit_confirmation_dialog();
            }
        })
    });

    function start_timer() {
        $.get(`/update_task_timing`, function(data) {
            console.log(data);
            console.log('timer starts (' + data.time_left + ') seconds left');
            console.log(data.half_session_time_left + ' seconds left in the current half of study session')
            if (data.time_left < 0)
                data.time_left = 0;
            task_time_out = setTimeout(function() {
                console.log('task time out');
                clearTimeout(task_time_out);
                if (data.half_session_time_left > data.time_left)
                    show_times_up_dialog();
                else
                    show_half_session_times_up_dialog();
            }, data.time_left * 1000);
        });
    }

    /* --- Terminal I/O --- */

    function set_websocket(container_port)  {
        protocol = (location.protocol === 'https:') ? 'wss://' : 'ws://';
        socketURL = protocol + location.hostname + `:10414/${container_port}`;

        /* var initialGeometry = term.proposeGeometry(),
          cols = initialGeometry.cols,
          rows = initialGeometry.rows;
        term.resize(cols, rows);
        charWidth = Math.ceil(term.element.offsetWidth / cols);
        charHeight = Math.ceil(term.element.offsetHeight / rows); */

        try {
            socket = new WebSocket(socketURL);
            socket.onopen = function() {
                console.log('WebSocket opened');

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
                    stdout += event.data;
                    // send the standard output to the backend whenever the user
                    // executes a command in the terminal
                    if (stdout.match(/(.|\n)*\@[0-9a-z]{12}\:[^\n]*\$ $/)) {
                        if (stdout.split('\n').length > 1) {
                            $.post(`/on_command_execution`, {stdout: stdout},
                                function(data) {
                                    console.log(data.status);
                                    refresh_vis(data);
                                    if (data.status == 'TASK_COMPLETED') {
                                        clearTimeout(task_time_out);
                                        if (is_training) {
                                            setTimeout(function() {
                                                show_training_completion_dialog(data);
                                            }, 300);
                                        } else {
                                            setTimeout(function() {
                                                show_task_completion_dialog();
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
        catch (err) {
            term.write('We are experiencing a shell connection error, please raise your hand.');
            // $.get(`/task_session_pause`);
        }
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

    function runRealTerminal() {
        term.attach(socket);
        term._initialized = true;
    }

    /* --- Visual Feedbacks --- */

    function refresh_vis(data) {

        // update treevis
        build_fs_tree_vis(data.filesystem_diff, "#current-tree-vis");

        // search in the tree for data exists a tag if val is null/ or value equals to val
        function exists_somewhere_in_tree(data, tag, val) {
            if (data.hasOwnProperty('tag') && data.tag.hasOwnProperty(tag)) {
                if (val == null || (data.tag[tag] == val))
                    return true;
            }
            if (data.hasOwnProperty('children')) {
                for(var i = 0; i < data.children.length; i ++) {
                    if (exists_somewhere_in_tree(data.children[i], tag, val))
                        return true;
                }
            }
            return false;
        };

        exists_fs_extra = exists_somewhere_in_tree(data.filesystem_diff, "extra", null);
        exists_fs_missing = exists_somewhere_in_tree(data.filesystem_diff, "missing", null);
        exists_select_missing = exists_somewhere_in_tree(data.filesystem_diff, "selected", -1);
        exists_select_wrong = exists_somewhere_in_tree(data.filesystem_diff, "selected", 1);
        exists_select_correct = exists_somewhere_in_tree(data.filesystem_diff, "selected", 1);

        exists_stdout_missing = false;
        exists_stdout_incorrect = false;
        if (data.hasOwnProperty('stdout_diff')) {
            for (var i = 0; i < data.stdout_diff.lines.length; i ++) {
                if (data.stdout_diff.lines[i].tag == "incorrect")
                    exists_stdout_incorrect = true;
                if (data.stdout_diff.lines[i].tag == "missing")
                    exists_stdout_missing  = true;
            }
        }



        $("#task-progress-vis").empty();
        $("#fs-vis-legend").empty();
        if (exists_fs_extra || exists_fs_missing || exists_select_missing 
            || exists_select_wrong || exists_stdout_incorrect || exists_stdout_missing) {
            // file system diff visualization
            $("#task-progress-vis").append('<div style="font-weight: bold;">You still have something more to work on...</div>');
            $("#task-progress-vis").append("<ol id='task-progress-report'></ol>");
        } else {
            $("#task-progress-vis").append('<div style="font-weight: bold;">No error! You are doing a perfect job.</div>');
            $("#task-progress-vis").append("<ol id='task-progress-report'></ol>");
        }

        // add explanation when fs mismatch
        var num_explanation_showing = 0;
        if (exists_fs_extra || exists_fs_missing) {
            var legend_content = "";
            if (exists_fs_extra) {
                $("#fs-vis-legend").append('<td><span style="color:red; text-decoration: line-through;"><span class="glyphicon glyphicon-file"></span>file extra</span></td>');
                legend_content += '<li>Files/Directories that are <b>extra</b> in your FS:\
                                    <span style="color:red; text-decoration: line-through;"><span class="glyphicon glyphicon-file"></span>file</span> or \
                                    <span style="color:red; text-decoration: line-through;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.\
                                    </li>';
                num_explanation_showing += 1;
            }
            if (exists_fs_missing) {
                $("#fs-vis-legend").append('<td><span style="opacity: 0.3;"><span class="glyphicon glyphicon-file"></span>file missing</span></td>');
                legend_content += '<li>Files/Directories <b>missing</b> in your current FS: \
                                    <span style="opacity: 0.3;"><span class="glyphicon glyphicon-file"></span>file</span> or \
                                    <span style="opacity: 0.3;"><span class="glyphicon glyphicon-folder-close"></span>dir</span></li>';
                num_explanation_showing += 1;
            }

            $("#task-progress-report").append('<li><font style="text-decoration: underline;">Your current filesystem status does not match the goal file system status (e.g., missing file, contain extra files).</font></li>');
            // add 
            // <ul class="legend-ul">' + legend_content + '</ul>
        }

        if (exists_select_wrong || exists_select_missing || exists_select_correct) {

            var legend_content = "";
            if (exists_select_missing) {
                $("#fs-vis-legend").append('<td><span style="background-color: #CCCCCC;"><span class="glyphicon glyphicon-file"></span>file not selected</span></td>');
                legend_content += '<li>Files/Directories your command <b>failed</b> to select: \
                            <span style="background-color: #CCCCCC;"><span class="glyphicon glyphicon-file"></span>file</span>,\
                            <span style="background-color: #CCCCCC;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.</li>';
                num_explanation_showing += 1;
            }

            if (exists_select_wrong) {
                $("#fs-vis-legend").append('<td><span style="background-color: #DF9496;"><span class="glyphicon glyphicon-file"></span>file incorrectly selected</span></td>');
                legend_content += '<li>Files/Directories your command <b>wrongly</b> selected: \
                                <span style="background-color: #DF9496;"><span class="glyphicon glyphicon-file"></span>file</span>,\
                                <span style="background-color: #DF9496;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.</li>';
                num_explanation_showing += 1;
            }

            if (exists_select_correct) {
                $("#fs-vis-legend").append('<td><span style="background-color: #FEFCD7;"><span class="glyphicon glyphicon-file"></span>file correctly selected</span></td>');
                legend_content += '<li>Files/Directories your command <b>correctly</b> selected: \
                               <span style="background-color: #FEFCD7;"><span class="glyphicon glyphicon-file"></span>file</span>,\
                               <span style="background-color: #FEFCD7;"><span class="glyphicon glyphicon-folder-close"></span>dir</span>.</li>';
                num_explanation_showing += 1;
            }

            $("#task-progress-report").append('<li><font style="text-decoration: underline;">Files/dirs selected by your command mismatches the desirable result.</font></li>');
        }
        if (num_explanation_showing == 0) {
            $("#current-tree-vis").css('bottom', '0px');
            $("#fs-vis-legend-container").height('0px');
            $("#fs-vis-legend-container").css('border-top', 'dashed 0px');
        } else if (num_explanation_showing > 2) {
            $("#current-tree-vis").css('bottom', '45px');
            $("#fs-vis-legend-container").height('45px');
            $("#fs-vis-legend-container").css('border-top', 'dashed 1px');
        } else {
            $("#current-tree-vis").css('bottom', '30px');
            $("#fs-vis-legend-container").height('30px');
            $("#fs-vis-legend-container").css('border-top', 'dashed 1px');
        }

        if (data.hasOwnProperty('stdout_diff')) {
            // console.log(data.filesystem_diff);
            // reset height of file system diff and stdout diff
            //$("#task-progress-container").show();
            //$("#current-tree-vis-container").css('bottom', '50%');

            $("#current-tree-vis-container").css("bottom", "50%");
            $("#task-progress-vis-container").css("top", "50.5%");

            missing_legend = "";
            if (exists_stdout_missing)
                missing_line_legend = '<li>There are lines <b>missing</b> in your print result: presented as "<span style="color:#CCCCCC">some line</span>".</li>';
            
            wrong_line_legend = "";
            if (exists_stdout_incorrect)
                wrong_line_legend = '<li>There are lines <b>wrongly printed</b>: presented as "<span style="color: red;text-decoration:line-through">some line</span>".</li>';


            if (exists_stdout_missing || exists_stdout_incorrect) {
                $("#task-progress-report").append('<li><font style="text-decoration: underline;">Your terminal output mismatches the solution output, see below</font>: \
                                                   <ul class="legend-ul" id="std-out-diff-legend">' + missing_line_legend + wrong_line_legend +
                                                    '<li>Your output v.s. solution output: <div id="std-out-diff" style="min-height:10px;border-style: dashed; padding-left:10px;"></div></li></ul>\
                                              </li>');
            } else {
                $("#task-progress-report").append('<li><font style="text-decoration: underline;">Your solution matches the goal output!</font>\
                                                   <ul class="legend-ul" id="std-out-diff-legend">\
                                                    <li>Your output v.s. solution output: <div id="std-out-diff" style="min-height:10px;border-style: dashed; padding-left:10px;"></div></li></ul>\
                                              </li>');
            }
            build_stdout_vis(data.stdout_diff, "#std-out-diff");
        }
    }

    /* --- Dialogs --- */

    function show_quit_confirmation_dialog(task_time_out) {
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
                    clearTimeout(task_time_out);
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

    function show_times_up_dialog() {
        // prompt the user that they have to move on to the next task
         BootstrapDialog.show({
             title: "Time's Up",
             message: "The current task session has timed out. Please proceed to the next task.",
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
    }

    function show_half_session_times_up_dialog() {
        // prompt the user that they have to move on to the next task
         BootstrapDialog.show({
             title: "Time's Up",
             message: "<p>You have spent 40 minutes using the current set of assistant tools. Good Job!</p> Please proceed to the next stage of the study.",
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
    }

    function show_task_completion_dialog() {
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
    }

    function show_training_completion_dialog(data) {
        $training_completion_acknowledgement = '<p>Awesome! You have completed the training session.</p>';
        $training_completion_acknowledgement += '<p> You are ready to start the task session. Remember that you may use ';
        if (data.treatment == 'A')
            $training_completion_acknowledgement += '<b>Tellina</b>, the Internet, and man pages for help at any time.<p>'
        else
            $training_completion_acknowledgement += '<b>Explainshell</b>, the Internet, and man pages for help at any time.<p>'
        BootstrapDialog.show({
            title: "Training: Completed",
            message: $training_completion_acknowledgement,
            buttons: [{
                label: "Proceed",
                cssClass: "btn-danger",
                action: function(dialogItself) {
                    dialogItself.close();
                    switch_task('passed');
                }
            }],
            closable: false
        });
    }

    /* function show_entering_stage_i_dialog(data) {
        var $stage_instruction = $('<div style="">');
        $stage_instruction.append('<p> When solving the first 8 tasks in the user study, you may use the following tools:');
        if (data.treatment_order == 0) {
            $stage_instruction.append('<ul><li><a href="' + data.research_tool_url + '" target="_blank">Tellina</a>, the natural language to bash translator</li><li>Any resources available in your bash terminal (s.a. man pages) or online (s.a. <a href="http://explainshell.com/" target="_blank">explainshell.com</a>).</li></ul></p>');
            $stage_instruction.append('<p>Especially, we encourage you to <b>try Tellina first</b> before accessing other tools.</p></div>');
        } else {
            $stage_instruction.append('<ul><li>Any resources available in your bash terminal (s.a. man pages) or online (s.a. <a href="http://explainshell.com/" target="_blank">explainshell.com</a>).</li></ul></p>');
            $stage_instruction.append('<p>However, you <b>cannot</b> use Tellina, the natural language to bash translator which was introduced in the training session.</p></div>')
        }
        BootstrapDialog.show({
            title: "You are ready to start the task session, please be reminded that",
            message: $stage_instruction,
            buttons: [{
                label: "Start Task Session",
                cssClass: "btn-primary",
                action: function(dialogItself) {
                    dialogItself.close();
                    window.location.replace(`http:\/\/${location.hostname}:10413/${data.task_session_id}`);
                }
            }],
            closable: false,
        });
    }

    function show_entering_stage_ii_dialog(data) {
        var $stage_instruction = $('<div style="">');
        if (data.treatment_order == 1) {
            $stage_instruction.append('<p> Starting from this point, you may use the following tool <b>in addition</b> to what you already have accessed so far:');
            $stage_instruction.append('<ul><li><a href="' + data.research_tool_url + '" target="_blank">Tellina</a>, the natural language to bash translator</li></ul></p>');
            $stage_instruction.append('<p>Especially, we encourage you to <b>try Tellina first</b> before accessing other tools.</p></div>');
        } else {
            $stage_instruction.append('<p> Starting from this point, please <b>stop</b> using Tellina when solving a task.</p>');
            $stage_instruction.append('<p>When you find yourself in need of help, please only resort to the <b>other resources</b> available online or in your bash terminal.</p></div>');
        }
        BootstrapDialog.show({
            title: "Nice job, you're half-way done!",
            message: $stage_instruction,
            buttons: [{
                label: "Resume Task Session",
                cssClass: "btn-primary",
                action: function(dialogItself) {
                    dialogItself.close();
                    window.location.replace(`http:\/\/${location.hostname}:10413/${data.task_session_id}`);
                }
            }],
            closable: false,
        });
    } */

    function switch_task(reason) {
        // close the websocket connection to the current container
        socket.close();
        $("button").attr("disabled", "disabled");

        // show wait dialog
        var $waitmsg = $('<div style="text-align: center;">Please wait while we are setting up the next task...</div>');
        $waitmsg.append('<br/>');
        $waitmsg.append('<img src="static/img/hourglass.gif" />');

        var wait_diaglog;
        var wait_diaglog_timeout = setTimeout(function () {
            wait_diaglog = BootstrapDialog.show({
                title: 'Keep Calm',
                message: $waitmsg,
                closable: false
            });
        }, 300);

        // set up the environment for the next task
        $.get(`/go_to_next_task`, {reason_for_close: reason}, function(data){
            clearTimeout(wait_diaglog_timeout);
            if (wait_diaglog != null)
                wait_diaglog.close();
            if (data.status == 'STUDY_SESSION_COMPLETE') {
                show_study_completion_dialog(data);
                console.log("Study session completed.");
            } else {
                normal_exit = true;
                window.location.replace(`http:\/\/${location.hostname}:10413/${data.task_session_id}`);
            }
        });
    }
});

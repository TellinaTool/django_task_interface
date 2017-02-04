/**
 * Define bootstrap dialog boxes and error messages used to interact with the
 * user during a task session.
 */

var filesystem_error_msg = "We've caught a file system error in the backend. Please try a few seconds later.";

/* --- Training Session Interactions --- */

function show_solution_dialog(solution) {
    // reveal the answer to the user when the quit button is clicked during the
    // training session
    var correct_answer = "The solution to this task is <code>" + solution + "</code>. Input this command in the terminal (without quotes) and observe the effect.";
    BootstrapDialog.show({
        title: "Solution",
        message: correct_answer,
        buttons: [
        {
            label: "Got it.",
            cssClass: "btn-danger",
            action: function(dialogItself) {
                dialogItself.close();
            }
        }]
    });
}

function show_training_task_i_assistant_tool_dialog(data) {
    var $instruction = '<div>' +
    '<p><i class="glyphicon glyphicon-info-sign"></i> When solving the first training task, you may use:';
    if (data.treatment_order == 0) {
        $instruction += '<ul><li><a href="' + data.research_tool_url + '" target="_blank">Tellina</a>, the natural language to bash translator</li><li>Any resources available in your bash terminal (s.a. man pages) or online (s.a. <a href="http://explainshell.com/" target="_blank">explainshell.com</a>).</li></ul></p>';
        $instruction += '<p>Especially, we encourage you to <b>try Tellina first</b> before accessing other tools.</p></div>';
    } else {
        $instruction += '<ul><li>Any resources available in your bash terminal (s.a. man pages) or online (s.a. <a href="http://explainshell.com/" target="_blank">explainshell.com</a>).</li></ul></p>';
        $instruction += '<p>However, you <b>cannot</b> use Tellina, the natural language to bash translator which you just tried out.</p></div>';
    }
    setTimeout(function () {
        BootstrapDialog.show({
            title: 'First Training Task',
            message: $instruction,
            buttons: [{
                label: "Got it",
                cssClass: "btn-danger",
                action: function(dialogItself) {
                    dialogItself.close();
                }
            }],
            closable: false
        });
    }, 300);
}

function show_training_task_ii_assistant_tool_dialog(data) {
    var $instruction = $('<div>');
    if (data.treatment_order == 1) {
        $instruction.append('<p><i class="glyphicon glyphicon-info-sign"></i> For the second training task, you may use <a href="' + data.research_tool_url + '" target="_blank">Tellina</a> <b>in addition to</b> what you have already accessed so far.</p>');
        $instruction.append('<p>Especially, we encourage you to <b>try Tellina first</b> before accessing other tools.</p></div>');
    } else {
        $instruction.append('<p><i class="glyphicon glyphicon-info-sign"></i> For the second training task, please <b>only</b> resort to the resources available in your bash terminal or online <b>except for Tellina</b>.</p></div>');
    }
    setTimeout(function () {
        BootstrapDialog.show({
            title: 'Second Training Task',
            message: $instruction,
            buttons: [{
                label: "Got it",
                cssClass: "btn-danger",
                action: function(dialogItself) {
                    dialogItself.close();
                }
            }],
            closable: false
        });
    }, 300);
}

/* --- Task Session Interactions --- */

function show_study_completion_dialog(report) {
    BootstrapDialog.show({
        title: "Congratulations, you have completed the study!",
        message: report + "\n\n" +
                "Please go on to fill in the post-study questionnaire.",
        buttons: [{
            label: "Go to questionnaire",
            cssClass: "btn-primary",
            action: function(dialogItself) {
                dialogItself.close();
                window.location.replace(`https://docs.google.com/a/cs.washington.edu/forms/d/e/1FAIpQLSdX1qM91hIG7mEy-6cTIbZ3b5iiUyMkytLHG3Mh03WFsACtvA/viewform`);
            }
        }],
        closable: false,
    });
}
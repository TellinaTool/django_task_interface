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

function start_task_platform_training(data) {
    var intro = introJs("#workspace").setOptions(task_platform_training)
    .setOption("tooltipClass", "img-overlay")
    .setOption('exitOnOverlayClick', false)
    .setOption('showBullets', false)
    .onchange(function(targetElement) {
        console.log(this._currentStep);
        switch (this._currentStep)
        {
            case 0:
                $('.img-overlay').css('max-width', '720px').css('min-width', '720px');
            break;
            case 11:
                $('.img-overlay').css('max-width', '400px').css('min-width', '400px');
            break;

            default:
                $('.img-overlay').css('max-width', '200px').css('min-width', '200px');
            break;
        }
        if (this._introItems.length - 1 == this._currentStep || this._introItems.length == 1) {
            $('.introjs-skipbutton').show();
        }
    })
    .oncomplete(function () {
        show_training_task_i_assistant_tool_dialog(data);
    })
    .start();
    $('.introjs-skipbutton').hide();
}

function show_training_task_i_assistant_tool_dialog(data) {
    var $instruction = '<div>' +
    '<p><i class="glyphicon glyphicon-info-sign"></i> For the first half of the study, you may use the following assistance:';
    if (data.treatment_order == 0) {
        title = 'Tellina';
        $instruction += '<ul><li><a href="' + data.research_tool_url + '" target="_blank">Tellina, a natural language to bash command translation tool</a>;</li><li>Any resources available in your bash terminal (such as man pages) or online.</li></ul></p>';
        $instruction += '<p>For each task, we encourage you to <b>try Tellina first</b>. Please click on the link above to learn more about the tool.</p>';
    } else {
        title = 'Explainshell';
        $instruction += '<ul><li><a href="http://explainshell.com/" target="_blank">Explainshell, a bash command explanation tool</a>;</li><li>Any resources available in your bash terminal (such as man pages) or online.</li></ul></p>';
        $instruction += '<p>We encourage you to <b>use Explainshell</b> when you encounter a bash command you do not completely understand. Please click on the link above to learn more about the tool.</p>';
    }
    $instruction += '<p>Once you are familiarized with the tool, please close this dialog box and complete the training task.</p></div>';
    setTimeout(function () {
        BootstrapDialog.show({
            title: title,
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
    var $instruction = '<div>' +
    '<p><i class="glyphicon glyphicon-info-sign"></i> For the second half of the study, you may use the following assistance:';
    if (data.treatment_order == 1) {
        title = 'Tellina';
        $instruction += '<ul><li><a href="' + data.research_tool_url + '" target="_blank">Tellina, a natural language to bash command translator</a>;</li><li>Any resources available in your bash terminal (such as man pages) or online (<b>including Explainshell</b>).</li></ul></p>';
        $instruction += '<p>For each task, we encourage you to <b>try Tellina first</b>. Please click on the link above to learn more about the tool.</p>';
    } else {
        title = 'Explainshell';
        $instruction += '<ul><li><a href="http://explainshell.com/" target="_blank">Explainshell, a bash command explanation tool</a>;</li><li>Any resources available in your bash terminal (such as man pages) or online (<b>excluding Tellina</b>).</li></ul></p>';
        $instruction += '<p>We encourage you to <b>use Explainshell</b> when you encounter a bash command you do not completely understand. Please click on the link above to learn more about the tool.</p>';
    }
    $instruction += '<p>Once you are familiarized with the tool, please close this dialog box and complete the training task.</p></div>';
    setTimeout(function () {
        BootstrapDialog.show({
            title: title,
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

function show_study_completion_dialog(data) {
    var report = "Report: passed " + data.num_passed + "/" + data.num_total +
        " tasks; given up " + data.num_given_up + "/" + data.num_total + " tasks.";
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
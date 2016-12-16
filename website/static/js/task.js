$(document).ready(function() {
    // task navigation
    $("#quit-button").click(function() {
        location.href = "/update_state";
    });

    $("#reset-button").click(function() {
        location.reload();
    });
})

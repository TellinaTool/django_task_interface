/**
 * Define task platform training tours, rendered by the hopscotch library.
 */

var init_fs_modification_training = {
    // The very first task the user encountered in the study is file system change.
    id: "init-fs-modification-training",
    showCloseButton: false,
    steps: [
        {
            title: "Bash user study tutorial",
            content: "Hey there! Welcome to the bash user study. This tutorial will guide you through it.",
            target: "task-platform-header",
            xOffset: 400,
            placement: "bottom"
        },
        {
            title: "Task Description",
            content: "The task description tells what your bash one-liner should do, such as modifying files or producing output.  (Don't try to do it yet.)",
            target: "task-description",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "Bash Terminal",
            content: "Execute commands in the bash terminal.  (Don't do it yet.)  The command can explore the file system, or can try to solve the goal.  If the command solves the goal, you will proceed to the next task.",
            target: "bash-terminal",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "Current File System",
            content: "Otherwise, if your command does not solve the goal, you can look here.  This panel visualizes a directory containing the source code for a website.  More importantly, it shows how the directory's current status, or the output of your command, is different than the goal status or output.  Each non-empty directory can be expanded or collapsed by a single click. Click on the \"content\" directory and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Realtime Result Check (1)",
            content: "The visualization is updated after each command.  Type \"rm index.html\" in the terminal (without the quotes) and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Realtime Result Check (2)",
            content: "If a command outputs file names, the listed files are also highlighted in the visualization. Type \"find content/\" in the terminal and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Reset File System",
            content: "This button resets the file system to its original state. Click it to bring back the \"index.html\" file you just deleted.",
            target: "reset-button",
            placement: "top",
            xOffset: -160,
            showPrevButton: true
        },
        {
            title: "Give Up On a Task",
            content: "If you are hopelessly stuck or frustrated on a particular task and more time will not help, you can move on to the next task.  The \"Give up\" button is disabled in this training tutorial.",
            target: "quit-button",
            placement: "top",
            showPrevButton: true
        },
        {
            title: "End of Instructions",
            content: "Now that you have learnt about every component on the platform, please go on to complete the training task. Raise your hand and let us know if you have any question.",
            target: "task-platform-header",
            placement: "bottom",
            xOffset: 400,
            showPrevButton: true
        }
    ]
};

var init_file_search_training = {
    // The very first task the user encountered in the study is file search.
    id: "init-file-search-training",
    showCloseButton: false,
    steps: [
        {
            title: "Bash user study tutorial",
            content: "Hey there! Welcome to the bash user study. This tutorial will guide you through it.",
            target: "task-platform-header",
            xOffset: 400,
            placement: "bottom"
        },
        {
            title: "Task Description",
            content: "The task description specifies relevant input values and the expected outcome.",
            target: "task-description",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "Current File System",
            content: "A visualization of your current directory is shown in this panel. It consists of the source code of a course website. Each non-empty directory can be expanded or collapsed by a single click. Click on the \"content\" directory and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Bash Terminal",
            content: "You will be interacting with the file system through the bash terminal. Execute a command here and the platform will automatically check if it does the specified operation. If the command is correct, you will proceed to the next task. Otherwise, you may keep trying.",
            target: "bash-terminal",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "More on Bash Terminal",
            content: "In addition, you may use the terminal to furthur explore the file system, it is supposed to be just like the shell on your computer.",
            target: "bash-terminal",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "Keep on Track",
            content: "To help you focusing on the right track, we marked up the files output by your last command execution and whether they match the expected output in the file system visualization.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Legend Explanation",
            content: "A node with light grey background indicates a file that should exists in the expected output but is not selected by the command you issued; a node with red background indicates a file that is in your output list but is not in the expected output; a node with bright yellow background indicates a correct output.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Realtime Result Check (1)",
            content: "The visualization is updated whenever you execute a command in the terminal. Type \"find content\" in the terminal and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Realtime Result Check (2)",
            content: "In addition, any change to your file system will also be shown in the visualization. Type \"rm index.html\" in the terminal and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Reset File System",
            content: "If you deleted files by mistake or have done any modification of file system which is unrecoverable, you may click the \"Reset\" button to reset the file system to its original state. Click on it to bring back the \"index.html\" file you just deleted.",
            target: "reset-button",
            placement: "top",
            xOffset: -160,
            showPrevButton: true
        },
        {
            title: "Time Limit",
            content: "You will be given maximum 10 minutes to complete each task. When time is up, you will be directed to the next one.",
            target: "reset-button",
            placement: "top",
            xOffset: -400,
            showPrevButton: true
        },
        {
            title: "Give Up On a Task",
            content: "If you are hopelessly stuck or frustrated on a particular task and more time will not help, you can move on to the next task.  The \"Give up\" button is disabled in this training tutorial.",
            target: "quit-button",
            placement: "top",
            showPrevButton: true
        },
        {
            title: "End of Instructions",
            content: "Now that you have learnt about every component on the platform, please go on to complete the training task. If you met any problem, please raise your hand and let us know.",
            target: "task-platform-header",
            placement: "bottom",
            xOffset: 400,
            showPrevButton: true
        }
    ]
};

/* var init_standard_output_training = {
    id: "init-standard-output-training",
    steps: [
        {
            title: "Bash user study tutorial",
            content: "Hey there! Welcome to the bash user study. This tutorial will guide you through it.",
            target: "task-platform-header",
            xOffset: 400,
            placement: "bottom"
        },
        {
            title: "Task Description",
            content: "The task description specifies relevant input values and the expected outcome.",
            target: "task-description",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "Current File System",
            content: "A visualization of your current directory is shown in this panel. It consists of the source code of a course website. Each non-empty directory can be expanded or collapsed by a single click. Click on the \"content\" directory and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Bash Terminal",
            content: "You will be interacting with the file system through the bash terminal. Execute a command here and the platform will automatically check if it does the specified operation. If the command is correct, you will proceed to the next task. Otherwise, you may keep trying.",
            target: "bash-terminal",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "More on Bash Terminal",
            content: "In addition, you may use the terminal to furthur explore the file system, it is supposed to be just like the shell on your computer.",
            target: "bash-terminal",
            placement: "right",
            showPrevButton: true
        },
        {
            title: "Keep on Track",
            content: "To help you focusing on the right track, we marked up the differences between your current directory and the goal in the file system visualization.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Realtime Result Check",
            content: "The visualization is updated whenever you execute a command in the terminal. Type \"rm index.html\" in the terminal and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Reset File System",
            content: "If you deleted files by mistake or have done any modification of file system which is unrecoverable, you may click the \"Reset\" button to reset the file system to its original state. Click on it to bring back the \"index.html\" file you just deleted.",
            target: "reset-button",
            placement: "top",
            xOffset: -160,
            showPrevButton: true
        },
        {
            title: "Time Limit",
            content: "You will be given maximum 10 minutes to complete each task. When time is up, you will be directed to the next one.",
            target: "reset-button",
            placement: "top",
            xOffset: -400,
            showPrevButton: true
        },
        {
            title: "Give Up a Task",
            content: "If you are hopelessly stuck or frustrated on a particular task and more time will not help, you can move on to the next task.  The \"Give up\" button is disabled in this training tutorial.",
            target: "quit-button",
            placement: "top",
            showPrevButton: true
        },
        {
            title: "End of Tutorial",
            content: "Thanks. You have finished this tutorial. Please go on to complete this training task. Raise your hand and let us know if you have any question.",
            target: "task-platform-header",
            placement: "bottom",
            xOffset: 400,
            showPrevButton: true
        }
    ]
}; */

/**
 * Define task platform training tours, rendered by the hopscotch library.
 */

var init_fs_modification_training = {
    // The very first task the user encountered in the study is file system operation.
    id: "init-fs-modification-training",
    showCloseButton: false,
    steps: [
        {
            title: "Task platform tutorial",
            content: "Hey there! Welcome to the Tellina user study platform. This tutorial will guide you through each component of it.",
            target: "task-platform-header",
            xOffset: 400,
            placement: "bottom"
        },
        {
            title: "Task",
            content: "You will see three types of file system operation tasks throughout the study sessions. The task in this tutorial asks you to perform file system modifications, such as to create/delete/modify specific files. You will be given additional tips when you encounter the other two types of tasks.",
            target: "task-description",
            placement: "right",
            showPrevButton: true
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
            title: "Legend Explanation",
            content: "If your current directory tree is different from the goal directory tree: a light grey node indicates a file exists in the goal directory that is missing from your current directory; a red node indicates a file exists in your current directory but is not contained in the goal directory.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Realtime Result Check (1)",
            content: "The visualization is updated whenever a command being executed results in a change in your file system. Type \"rm index.html\" in the terminal and observe the effect.",
            target: "current-tree-vis",
            placement: "left",
            showPrevButton: true
        },
        {
            title: "Realtime Result Check (2)",
            content: "In addition, if you issued a command which lists some files on the terminal, the listed files will also be highlighted in the visualization. Type \"find content/\" in the terminal and observe the effect.",
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
            title: "(Not Encouraged) Give Up a Task",
            content: "We hope you can try your best and make use of all the allocated time for each task. However, occassionally you may find yourself stuck with a particular task and more time will not help. In this case you may click the \"Give up\" button to proceed to the next one. Keep in mind that the use of the \"Give up\" button is disabled in this training tutorial and is strongly discouraged in the real tasks.",
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
            title: "Task platform tutorial",
            content: "Hey there! Welcome to the Tellina user study platform. This tutorial will guide you through each component of it.",
            target: "task-platform-header",
            xOffset: 400,
            placement: "bottom"
        },
        {
            title: "Task",
            content: "You will see three types of file system operation tasks throughout the study sessions. The task in this tutorial asks you to list files that have certain properties in the terminal. You will be given additional tips when you encounter the other two types of tasks.",
            target: "task-description",
            placement: "right",
            showPrevButton: true
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
            title: "(Not Encouraged) Give Up a Task",
            content: "We hope you can try your best and make use of all the allocated time for each task. However, occassionally you may find yourself stuck with a particular task and more time will not help. In this case you may click the \"Give up\" button to proceed to the next one. Keep in mind that the use of the \"Give up\" button is disabled in this training tutorial and is strongly discouraged in the real tasks.",
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
            title: "Task platform tutorial",
            content: "Hey there! Welcome to the Tellina user study platform. This tutorial will guide you through each component of it.",
            target: "task-platform-header",
            xOffset: 400,
            placement: "bottom"
        },
        {
            title: "Task",
            content: "You will see three types of file system operation tasks throughout the study sessions. The task in this tutorial requires you to perform file system modifications, such as to create/delete/modify specific files. You will be given additional tips when you encounter the other two types of tasks.",
            target: "task-description",
            placement: "right",
            showPrevButton: true
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
            title: "Legend Explanation",
            content: "If your current directory tree is different from the goal directory tree: a light grey node indicates a file exists in the goal directory that is missing from your current directory; a red node indicates a file exists in your current directory but is not contained in the goal directory.",
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
            title: "(Not Encouraged) Give Up a Task",
            content: "We hope you can try your best and make use of all the allocated time for each task. However, occassionally you may find yourself stuck with a particular task and more time will not help. In this case you may click the \"Give up\" button to proceed to the next one. Keep in mind that the use of the \"Give up\" button is disabled in this training tutorial and is strongly discouraged in the real tasks.",
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

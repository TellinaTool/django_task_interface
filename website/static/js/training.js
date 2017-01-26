/**
 * Define task platform training tours, rendered by the hopscotch library.
 */

var task_platform_training = {
    steps: [
        {
            element: "#img-overlay-hanger",
            intro: "<div style=\"font-size: 12px\"><p>Welcome to the task platform training!</p><p>The task platform consists of three main conponents (as illustrated below):<ul><li>the task description</li><li>the bash terminal</li><li>a visualization of your file system status and your progress in the task.</li></ul></p></div><img src=\"static/img/task_platform.png\" height=\"100%\" width=\"100%\"></img><br>",
        },
        {
            element: "#task-description",
            intro: "The task description tells what your bash command should do, such as modifying files or producing output.",
            position: "right"
        },
        {
            element: "#bash-container",
            intro: "Execute your commands in the bash terminal. The command may solve the task or explore the file system.  If the command solves the task, you will proceed to the next task.",
            position: "right"
        },
        {
            element: "#current-tree-vis-container",
            intro: "Otherwise, if your command does not solve the goal, you can look here.  This panel visualizes a directory containing the source code for a website.  More importantly, it shows how the directory's current status, or the output of your command, is different than the goal status or output.  Each non-empty directory can be expanded or collapsed by a single click. Click on the \"content\" directory and observe the effect.",
            position: "left"
        },
        {
            element: "#bash-container",
            intro: "The visualization is updated after each command.  Type \"rm index.html\" in the terminal (without the quotes) and observe the effect.",
            position: "right"
        },
        {
            element: "#current-tree-vis-container",
            intro: "The icon of \"index.html\" turned grey, indicating that it has been deleted from your file system",
            position: "left"
        },
        {
            element: "#bash-container",
            intro: "If a command outputs file names, the listed files are also highlighted in the visualization. Type \"find css/\" in the terminal and observe the effect.",
            position: "right"
        },
        {
            element: "#current-tree-vis-container",
            intro: "You have just selected all files and directories under the \"css\" directory. The files highlighted in yellow are in the desired output. The two directories are highlighted in red, since they are not in the desired output.",
            position: "left"
        },
        {
            element: "#reset-button",
            intro: "This button resets the file system to its original state. Click it to bring back the \"index.html\" file you just deleted.",
            position: "top"
        },
        {
            element: "#quit-button",
            intro: "If you are hopelessly stuck or frustrated on a particular task and more time will not help, you can move on to the next task.  The \"Give up\" button is disabled in this training tutorial.",
            position: "top"
        },
        {
            element: "#img-overlay-hanger",
            intro: "Now that you have learnt about every component on the platform, please go on to complete the two training tasks. Raise your hand and let us know if you have any question.",
            position: "bottom"
        }
    ]
};

var tellina_google_training_first = {};

var google_training_first = {};

var tellina_google_training_second = {};

var google_training_second = {};

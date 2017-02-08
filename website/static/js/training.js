/**
 * Define task platform training tours, rendered by the intro.js library.
 */

var task_platform_training = {
    steps: [
        {
            element: "#img-overlay-hanger",
            intro: "<div style=\"\"><p>Hey there! This tutorial will familiarize you with the task platform before you start.</p><p>The platform consists of three main components:<ul><li>the task description</li><li>the bash terminal</li><li>the visualization of your current filesystem and your working progress.</li></ul></p></div><img src=\"static/img/task_platform.png\" height=\"100%\" width=\"100%\"></img><br>",
        },
        {
            element: "#task-description",
            intro: "The task description specifies what your bash command should do, such as modifying files or producing output.",
            position: "right"
        },
        {
            element: "#bash-container",
            intro: "<p>Execute all your commands in the bash terminal.</p> <p>If the command solves the task, you will proceed to the next task.</p>",
            position: "right"
        },
        {
            element: "#current-tree-vis-container",
            intro: "<p>Otherwise, if your command does not solve the goal, you can look here. This panel visualizes your filesystem and how it differs from the goal filesystem.</p> <p>Each non-empty directory can be expanded or collapsed by a single click. Click on the \"content\" directory and expand it.</p>",
            position: "left"
        },
        {
            element: "#task-progress-vis-container",
            intro: "<p>If a task requires you to print specific content on the terminal, the lower right panel will show the difference between your terminal output and the goal output.</p> <p>Otherwise, it will be minimized.",
            position: "left"
        },
        {
            element: "#bash-container",
            intro: "The visualization is updated after each command execution.  Type <code>rm index.html</code> in the terminal (without the quotes) and observe the effect.",
            position: "right"
        },
        {
            element: "#task-progress-container",
            intro: "The icon of \"index.html\" turned grey, indicating that it has been deleted from your file system.",
            position: "left"
        },
        {
            element: "#bash-container",
            intro: "If a command outputs file names, the listed files are also highlighted in the visualization. Type <code>find css</code> in the terminal and observe the effect.",
            position: "right"
        },
        {
            element: "#task-progress-container",
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
            intro: '<div style=""><p>Now that you have learned about the task platform, please go on to complete the training task with the assistant tool we are going to introduce next and other resources.</p></div>',
            position: "bottom"
        }
    ]
};

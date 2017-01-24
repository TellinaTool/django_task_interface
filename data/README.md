## About this folder

This folder contains (1) the sample configuration file for a task, (2) a copy of the file system used in the task platform (example-website.tar.xz) and (3) the descriptions of all tasks used in our user study.

## The sample configuration file `config.sample.json`

You can make the sample configuration file real using the commnad: `cp config.sample.json config.json`.

The example file is for an experiment with the following setup,
but you can customize any of these aspects of the experiment:

* Each task takes 300 seconds.
* There are 2 participants: `bob` and `alice`.
* There are 2 tasks:
  1. Print hello world.
    * Initial filesystem: none
    * Answer: `hello world` is in standard output
  2. Create a file named `hello.txt` in `~/dir1/dir2`.
    * Initial file system:

       ```
       dir1/
       file.txt
         dir2/
       ```

    * Answer: user's home directory should look like

       ```
       dir1/
       file.txt
         dir2/
           hello.txt
       ```

## Extract the file system copy

The command below prepares the file system copy that will be used in the user study tasks.

```
tar xvf example_website.tar.xz
```

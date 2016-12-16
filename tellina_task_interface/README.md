This is the default application created when you run
`django-admin startproject tellina_task_interface`. It is generally recommended
that you put your main application code in a separate Django application (see
the `website/` folder), even if your project has only 1 application.

I only edited

* `settings.py` to configure various server settings
* `urls.py` to route requests to the actual application in `website/`.

"""
This file routes URLs to handler functions.
"""

from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    url(r'^initialize_task$', views.initialize_task),
    url(r'^get_filesystem$', views.get_filesystem),
    url(r'^check_task_state$', views.check_task_state),
    url(r'^update_state$', views.update_state),

    # login page
    url(r'^user_login$', views.user_login),
    url(r'^register_user$', views.register_user),
    url(r'^retrieve_access_code$', views.retrieve_access_code),

    # study session
    url(r'^get_container_port$', views.get_container_port),

    # task session
    url(r'^.*-study_session-.*/task-.*', views.task),
    url(r'^get_task$', views.get_task),

    # admin page
    url(r'^admin', admin.site.urls),

    url(r'^', TemplateView.as_view(template_name='login.html'),
        name='home'),
    url(r'^append_stdin$', views.append_stdin),
    url(r'^append_stdout$', views.append_stdout),
]

"""
This file routes URLs to handler functions.
"""

from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    # login page
    url(r'^user_login$', views.user_login),
    url(r'^register_user$', views.register_user),
    url(r'^retrieve_access_code$', views.retrieve_access_code),

    # task session
    url(r'^.*-study_session-.*/task-.*', views.get_current_task),
    url(r'^get_current_task$', views.get_current_task),
    url(r'^get_additional_task_info$', views.get_additional_task_info),
    url(r'^go_to_next_task$', views.go_to_next_task),
    url(r'^instruction$', views.instruction),

    # terminal I/O
    url(r'^on_command_execution$', views.on_command_execution),

    # file system
    url(r'^reset_file_system', views.reset_file_system),

    # admin page
    url(r'^admin', admin.site.urls),

    url(r'^', TemplateView.as_view(template_name='login.html'),
        name='home'),

    # url(r'^initialize_task$', views.initialize_task),
    # url(r'^get_filesystem$', views.get_filesystem),
    # url(r'^check_task_state$', views.check_task_state),
    # url(r'^update_state$', views.update_state),
    # url(r'^append_stdin$', views.append_stdin),
]

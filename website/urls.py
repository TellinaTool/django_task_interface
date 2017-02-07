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
    url(r'^resume_task_session$', views.resume_task_session),

    # consent & instruction
    url(r'^consent$', views.consent),
    url(r'^consent_signed$', views.consent_signed),
    url(r'^instruction$', views.instruction),
    url(r'^instruction_read$', views.instruction_read),

    # task session
    url(r'^.*-study_session-.*-task-.*', views.get_current_task),
    url(r'^update_task_timing$', views.update_task_timing),
    url(r'^get_current_task$', views.get_current_task),
    url(r'^get_additional_task_info$', views.get_additional_task_info),
    url(r'^go_to_next_task$', views.go_to_next_task),
    url(r'^task_session_paused$', views.task_session_paused),

    # terminal I/O
    url(r'^on_command_execution$', views.on_command_execution),

    # file system
    url(r'^reset_file_system$', views.reset_file_system),

    # admin pagedj
    url(r'^admin', admin.site.urls),
    url(r'^study_session_report.*', views.study_session_report),
    url(r'^overview$', views.overview),

    # login & registration
    url(r'', TemplateView.as_view(template_name='login.html'),
        name='home'),
]

